"""
StreamPulse Configuration Manager
Loads configuration from environment variables and CLI overrides.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env if present
load_dotenv()


@dataclass
class Config:
    # Stream settings
    stream_url: str = ""
    interval_seconds: int = 180  # Batch every 3 minutes
    history_lookback: int = 3    # Keep previous 3 chunks for context

    # Transcription
    whisper_model: str = "base"  # tiny, base, small, medium
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    language: Optional[str] = None  # None for auto-detect, or 'de', 'en'

    # LLM Settings
    llm_provider: str = "gemini"  # gemini, openai, groq, ollama
    gemini_api_key: Optional[str] = field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    groq_api_key: Optional[str] = field(default_factory=lambda: os.getenv("GROQ_API_KEY"))
    llm_model: str = "gemini-1.5-flash"
    llm_base_url: Optional[str] = field(default_factory=lambda: os.getenv("LLM_BASE_URL"))

    # Twitter / X API
    twitter_consumer_key: Optional[str] = field(default_factory=lambda: os.getenv("TWITTER_CONSUMER_KEY"))
    twitter_consumer_secret: Optional[str] = field(default_factory=lambda: os.getenv("TWITTER_CONSUMER_SECRET"))
    twitter_access_token: Optional[str] = field(default_factory=lambda: os.getenv("TWITTER_ACCESS_TOKEN"))
    twitter_access_token_secret: Optional[str] = field(default_factory=lambda: os.getenv("TWITTER_ACCESS_TOKEN_SECRET"))
    twitter_bearer_token: Optional[str] = field(default_factory=lambda: os.getenv("TWITTER_BEARER_TOKEN"))

    # Discord / Slack Webhook
    discord_webhook_url: Optional[str] = field(default_factory=lambda: os.getenv("DISCORD_WEBHOOK_URL"))

    # Behavior & Output
    dry_run: bool = False
    auto_publish: bool = True
    capture_screenshots: bool = True
    output_dir: Path = Path("./output")
    live_feed_file: Path = Path("./output/live_feed.md")

    # Tone & Formatting
    tone: str = "engaging, insightful, tech-forward, authoritative"
    stream_topic: str = "General Live Stream"
    hashtags_preset: str = ""

    def __post_init__(self):
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "screenshots").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "audio").mkdir(parents=True, exist_ok=True)
        self.live_feed_file = Path(self.live_feed_file)
