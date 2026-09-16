"""
Transcription Engine for StreamPulse
Zero-API-cost dual transcription:
1. YouTube Live Captions / Subtitles (Instant, 0 CPU)
2. Local faster-whisper on CPU/GPU (Offline, 0 API tokens)
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from streampulse.utils import console

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None


class Transcriber:
    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        language: Optional[str] = None
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self._whisper_instance: Optional[WhisperModel] = None

    def _get_whisper(self) -> WhisperModel:
        """Lazy loader for faster-whisper to conserve RAM when not needed."""
        if self._whisper_instance is None:
            if WhisperModel is None:
                raise RuntimeError("faster-whisper is not installed.")
            console.log(f"[cyan]Initializing faster-whisper ({self.model_size}, {self.device}, {self.compute_type})...[/cyan]")
            self._whisper_instance = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
        return self._whisper_instance

    def transcribe_audio_file(self, audio_path: Path) -> Dict[str, Any]:
        """
        Transcribes a local audio chunk using faster-whisper.
        Returns dictionary with text, language, and segments.
        """
        whisper = self._get_whisper()
        console.log(f"[dim]Transcribing {audio_path.name}...[/dim]")
        
        segments_generator, info = whisper.transcribe(
            str(audio_path),
            beam_size=5,
            language=self.language,
            vad_filter=True  # Voice activity detection to skip silence
        )

        segments = list(segments_generator)
        full_text = " ".join([seg.text.strip() for seg in segments]).strip()

        return {
            "text": full_text,
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "segments": [
                {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
                for seg in segments
            ]
        }

    def try_fetch_youtube_transcript(self, video_id: str, languages: Optional[List[str]] = None) -> Optional[str]:
        """
        Attempts to fetch YouTube captions if the video is a Premiere or has pre-uploaded tracks.
        """
        if YouTubeTranscriptApi is None:
            return None
        
        langs = languages or ["de", "en"]
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=langs)
            full_text = " ".join([entry["text"] for entry in transcript_list])
            return full_text
        except Exception:
            return None
