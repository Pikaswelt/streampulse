"""
AI Content Analyzer & Social Post Crafter
Evaluates stream transcript chunks, identifies breaking highlights,
and crafts viral, high-value X (Twitter) posts.
"""

import json
import re
from typing import Dict, Any, List, Optional
import requests
from streampulse.utils import console, fit_tweet_length, calculate_tweet_length


SYSTEM_PROMPT = """You are an elite live-tweeting AI journalist and social media strategist.
Your task is to monitor a live stream or Premiere transcript and craft high-impact, authentic posts for X (Twitter).

CRITICAL RULES:
1. FILTER OUT NOISE: Only trigger a tweet if there is a genuine highlight, new announcement, strong quote, surprising insight, or key takeaway.
   If the segment is just intro, smalltalk, technical pauses, or repetitive filler, set "is_highlight": false.
2. TWEET LENGTH: Maximum 280 characters. Every character counts!
3. ENGAGEMENT STYLE:
   - Punchy first line (hook).
   - Core revelation, stat, or direct quote.
   - Include 1-2 relevant, clean hashtags.
   - Professional, forward-thinking, hype when appropriate.
4. LANGUAGE: Match the language of the transcript unless specified otherwise.
5. OUTPUT: Output ONLY a valid JSON object matching this schema:
{
  "is_highlight": boolean,
  "reason": "Brief explanation why or why not",
  "tweet": "The drafted tweet text (<= 280 chars)",
  "quote": "Key direct quote if any",
  "key_takeaway": "Short 1-sentence bullet point",
  "suggested_tags": ["#tag1", "#tag2"]
}
"""


class ContentAnalyzer:
    def __init__(
        self,
        provider: str = "gemini",
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-flash",
        base_url: Optional[str] = None,
        tone: str = "authoritative, insightful, engaging",
        stream_topic: str = "General Live Event"
    ):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.tone = tone
        self.stream_topic = stream_topic

    def analyze_chunk(
        self,
        current_transcript: str,
        recent_history: List[str],
        timestamp_sec: int = 0
    ) -> Dict[str, Any]:
        """
        Analyzes the current transcript segment and returns a JSON dict.
        """
        if not current_transcript or len(current_transcript.strip()) < 30:
            return {
                "is_highlight": False,
                "reason": "Segment too short or empty",
                "tweet": "",
                "quote": "",
                "key_takeaway": ""
            }

        prompt = f"""
Stream Topic: {self.stream_topic}
Desired Tone: {self.tone}
Current Timestamp: ~{timestamp_sec // 60}m {timestamp_sec % 60}s into the stream

RECENT PREVIOUS EVENTS (for context, do not duplicate):
{chr(10).join(recent_history[-3:]) if recent_history else "Stream just started."}

NEW TRANSCRIPT SEGMENT TO EVALUATE:
\"\"\"{current_transcript}\"\"\"

Analyze this segment and respond with ONLY the JSON object.
"""

        # 1. Gemini Provider
        if self.provider == "gemini" and self.api_key:
            return self._call_gemini(prompt)

        # 2. OpenAI / Groq / Ollama / OpenRouter Provider
        if (self.provider in ["openai", "groq", "ollama"] and self.api_key) or (self.provider == "ollama" and self.base_url):
            return self._call_openai_compatible(prompt)

        # 3. Fallback Heuristic Analyzer (0 API Keys required)
        return self._fallback_heuristic_analyzer(current_transcript, timestamp_sec)

    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\n" + prompt}]}],
            "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json"}
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return self._clean_and_parse_json(raw_text)
        except Exception as e:
            console.log(f"[yellow]Gemini API error ({e}), falling back to heuristic[/yellow]")
            return self._fallback_heuristic_analyzer(prompt)

    def _call_openai_compatible(self, prompt: str) -> Dict[str, Any]:
        base_url = self.base_url
        if not base_url:
            if self.provider == "groq":
                base_url = "https://api.groq.com/openai/v1"
            elif self.provider == "ollama":
                base_url = "http://localhost:11434/v1"
            else:
                base_url = "https://api.openai.com/v1"

        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key or 'ollama'}"
        }
        payload = {
            "model": self.model if self.model != "gemini-1.5-flash" else "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4,
            "response_format": {"type": "json_object"}
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["choices"][0]["message"]["content"]
            return self._clean_and_parse_json(raw_text)
        except Exception as e:
            console.log(f"[yellow]OpenAI-compatible API error ({e}), falling back to heuristic[/yellow]")
            return self._fallback_heuristic_analyzer(prompt)

    def _fallback_heuristic_analyzer(self, text: str, timestamp_sec: int = 0) -> Dict[str, Any]:
        """
        Lightweight NLP heuristic when no API key is available or during offline dry-runs.
        Selects salient sentences and wraps them into a clean tweet format.
        """
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 20]
        if not sentences:
            return {"is_highlight": False, "reason": "No clear sentences found"}

        # Find best sentence (longest or containing keywords)
        keywords = ["neu", "launch", "release", "announce", "important", "future", "update", "vision", "ai", "feature", "jetzt"]
        best_sentence = max(sentences, key=lambda s: sum(2 for k in keywords if k in s.lower()) + len(s) / 50)
        
        minutes = timestamp_sec // 60
        tweet_draft = f"🔴 Live Update [{minutes:02d}:00]: \"{best_sentence}\" #LiveStream"
        tweet_draft = fit_tweet_length(tweet_draft, 280)

        return {
            "is_highlight": True,
            "reason": "Salient event detected via heuristic",
            "tweet": tweet_draft,
            "quote": best_sentence,
            "key_takeaway": best_sentence,
            "suggested_tags": ["#LiveStream"]
        }

    def _clean_and_parse_json(self, raw_text: str) -> Dict[str, Any]:
        """Strip markdown fences and parse json."""
        cleaned = re.sub(r"^```json\s*", "", raw_text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"^```\s*", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
        data = json.loads(cleaned)
        
        # Ensure tweet length safety
        if "tweet" in data and data["tweet"]:
            data["tweet"] = fit_tweet_length(data["tweet"], 280)
            
        return data
