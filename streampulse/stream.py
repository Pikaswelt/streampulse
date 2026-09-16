"""
Stream Capture Engine
Interacts with yt-dlp and ffmpeg to fetch audio and snapshots from YouTube streams.
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from streampulse.utils import console


class StreamCapture:
    def __init__(self, stream_url: str, output_dir: Path):
        self.stream_url = stream_url
        self.output_dir = output_dir
        self.audio_dir = output_dir / "audio"
        self.screenshot_dir = output_dir / "screenshots"
        self.metadata: Dict[str, Any] = {}
        self.live_stream_url: Optional[str] = None
        self.is_live: bool = False

    def fetch_metadata(self) -> Dict[str, Any]:
        """Fetch video/stream metadata using yt-dlp."""
        console.log(f"[cyan]Fetching stream metadata for:[/cyan] {self.stream_url}")
        cmd = [
            "yt-dlp",
            "--js-runtimes", "node",
            "--dump-json",
            "--skip-download",
            "--ignore-no-formats-error",
            "--no-warnings",
            self.stream_url,
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.metadata = json.loads(res.stdout)
            self.is_live = bool(self.metadata.get("is_live") or self.metadata.get("was_live"))
            status = self.metadata.get("live_status", "unknown")
            console.log(f"[green]Detected:[/green] '{self.metadata.get('title')}' by {self.metadata.get('uploader')} [Status: {status}]")
            return self.metadata
        except subprocess.CalledProcessError as e:
            console.log(f"[red]Error fetching metadata:[/red] {e.stderr}")
            raise RuntimeError(f"Could not inspect YouTube stream: {e.stderr}")

    def wait_until_live(self, poll_interval_sec: int = 10):
        """Wait until scheduled premiere goes live."""
        console.log("[cyan]Checking if stream is live yet...[/cyan]")
        while True:
            meta = self.fetch_metadata()
            status = meta.get("live_status")
            if status in ["is_live", "was_live"] or not status:
                console.log("[bold green]Stream is LIVE! Commencing capture...[/bold green]")
                break
            console.log(f"[dim]Status is '{status}'. Waiting {poll_interval_sec}s for premiere to begin...[/dim]")
            time.sleep(poll_interval_sec)

    def get_direct_stream_urls(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract direct audio and video stream URLs using yt-dlp.
        Returns (audio_stream_url, video_stream_url)
        """
        cmd = [
            "yt-dlp",
            "-g",
            "--no-warnings",
            self.stream_url
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            lines = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
            if len(lines) >= 2:
                # Video format URL, Audio format URL
                return lines[1], lines[0]
            elif len(lines) == 1:
                return lines[0], lines[0]
            return None, None
        except subprocess.CalledProcessError as e:
            console.log(f"[yellow]Failed to extract direct stream url: {e.stderr}[/yellow]")
            return None, None

    def capture_audio_chunk(self, duration_sec: int = 180, chunk_idx: int = 1) -> Path:
        """
        Captures a chunk of audio from the stream of length duration_sec.
        Saves as mono 16kHz MP3/WAV suitable for Whisper transcription.
        """
        output_file = self.audio_dir / f"chunk_{chunk_idx:04d}_{int(time.time())}.wav"

        # Using yt-dlp pipe directly into ffmpeg is most reliable for live streams
        # yt-dlp -o - <url> | ffmpeg -i pipe:0 -t <duration> -ar 16000 -ac 1 output.wav
        console.log(f"[dim]Recording {duration_sec}s audio chunk #{chunk_idx}...[/dim]")
        
        ytdlp_cmd = [
            "yt-dlp",
            "--js-runtimes", "node",
            "--wait-for-video", "5",
            "-f", "ba/b",
            "-o", "-",
            "--no-warnings",
            self.stream_url
        ]
        
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-loglevel", "error",
            "-i", "pipe:0",
            "-t", str(duration_sec),
            "-ar", "16000",
            "-ac", "1",
            str(output_file)
        ]

        ytdlp_proc = subprocess.Popen(ytdlp_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            subprocess.run(ffmpeg_cmd, stdin=ytdlp_proc.stdout, check=True)
            ytdlp_proc.stdout.close()
            ytdlp_proc.wait(timeout=duration_sec + 15)
        except Exception as e:
            ytdlp_proc.kill()
            raise RuntimeError(f"Audio chunk capture failed: {e}")

        return output_file

    def capture_screenshot(self, screenshot_idx: int = 1) -> Optional[Path]:
        """
        Captures a crisp high-res screenshot from the current live stream frame.
        """
        output_file = self.screenshot_dir / f"frame_{screenshot_idx:04d}_{int(time.time())}.jpg"
        
        # Capture 1 video frame using yt-dlp + ffmpeg
        ytdlp_cmd = [
            "yt-dlp",
            "--js-runtimes", "node",
            "--wait-for-video", "5",
            "-f", "bv/b",
            "-o", "-",
            "--no-warnings",
            self.stream_url
        ]
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-loglevel", "error",
            "-i", "pipe:0",
            "-ss", "00:00:01",
            "-vframes", "1",
            "-q:v", "2",
            str(output_file)
        ]

        ytdlp_proc = subprocess.Popen(ytdlp_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            subprocess.run(ffmpeg_cmd, stdin=ytdlp_proc.stdout, timeout=25, check=True)
            ytdlp_proc.stdout.close()
            ytdlp_proc.wait(timeout=5)
            if output_file.exists() and output_file.stat().st_size > 1000:
                return output_file
        except Exception as e:
            ytdlp_proc.kill()
            console.log(f"[dim yellow]Warning: Screenshot capture skipped ({e})[/dim yellow]")
            return None

        return None
