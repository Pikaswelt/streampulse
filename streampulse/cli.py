"""
StreamPulse CLI Entrypoint
"""

import argparse
import sys
import time
from pathlib import Path
from streampulse.config import Config
from streampulse.stream import StreamCapture
from streampulse.transcriber import Transcriber
from streampulse.analyzer import ContentAnalyzer
from streampulse.publisher import Publisher
from streampulse.utils import console
from rich.panel import Panel
from rich.table import Table


def print_banner():
    banner_text = """
 [bold cyan]   _____ __                               ____        __             [/bold cyan]
 [bold cyan]  / ___// /_________  ____ _____ ___     / __ \__  __/ /_______      [/bold cyan]
 [bold cyan]  \__ \/ __/ ___/ _ \/ __ `/ __ `__ \   / /_/ / / / / / ___/ _ \     [/bold cyan]
 [bold cyan] ___/ / /_/ /  /  __/ /_/ / / / / / /  / ____/ /_/ / (__  )  __/     [/bold cyan]
 [bold cyan]/____/\__/_/   \___/\__,_/_/ /_/ /_/  /_/    \__,_/_/____/\___/  AI  [/bold cyan]
    """
    console.print(banner_text, style="cyan")
    console.print("[dim cyan]Real-Time YouTube Live to X (Twitter) AI Agent | Zero API Waste[/dim cyan]\n")


def cmd_run(args):
    print_banner()
    config = Config(
        stream_url=args.url,
        interval_seconds=args.interval,
        whisper_model=args.whisper_model,
        language=args.lang,
        llm_provider=args.provider,
        llm_model=args.llm_model,
        dry_run=args.dry_run,
        capture_screenshots=not args.no_screenshots,
        stream_topic=args.topic or "Live YouTube Event",
        tone=args.tone or "insightful, forward-thinking, engaging",
        discord_webhook_url=args.webhook
    )

    console.print(Panel(
        f"[bold]Stream URL:[/bold] {config.stream_url}\n"
        f"[bold]Interval:[/bold] {config.interval_seconds}s | [bold]Whisper Model:[/bold] {config.whisper_model}\n"
        f"[bold]LLM Provider:[/bold] {config.llm_provider} ({config.llm_model})\n"
        f"[bold]Mode:[/bold] {'[yellow]DRY-RUN (Simulated Posting)[/yellow]' if config.dry_run else '[green]LIVE POSTING TO X[/green]'}\n"
        f"[bold]Live Markdown Feed:[/bold] {config.live_feed_file}",
        title="[bold green]Configuration Loaded[/bold green]",
        border_style="green"
    ))

    # Initialize modules
    stream_engine = StreamCapture(config.stream_url, config.output_dir)
    transcriber = Transcriber(
        model_size=config.whisper_model,
        device=config.whisper_device,
        compute_type=config.whisper_compute_type,
        language=config.language
    )
    analyzer = ContentAnalyzer(
        provider=config.llm_provider,
        api_key=config.gemini_api_key if config.llm_provider == "gemini" else config.openai_api_key or config.groq_api_key,
        model=config.llm_model,
        base_url=config.llm_base_url,
        tone=config.tone,
        stream_topic=config.stream_topic
    )
    publisher = Publisher(
        consumer_key=config.twitter_consumer_key,
        consumer_secret=config.twitter_consumer_secret,
        access_token=config.twitter_access_token,
        access_token_secret=config.twitter_access_token_secret,
        bearer_token=config.twitter_bearer_token,
        discord_webhook_url=config.discord_webhook_url,
        live_feed_path=config.live_feed_file,
        dry_run=config.dry_run
    )

    # Fetch initial stream metadata
    try:
        metadata = stream_engine.fetch_metadata()
        console.log(f"[bold green]Connected to stream:[/bold green] {metadata.get('title')}")
    except Exception as e:
        console.log(f"[bold yellow]Stream check notice:[/bold yellow] {e}")

    chunk_idx = 0
    recent_history = []
    total_elapsed_sec = 0

    console.log(f"[bold green]Starting StreamPulse monitoring loop (Press Ctrl+C to stop)...[/bold green]")

    try:
        while True:
            chunk_idx += 1
            console.rule(f"[bold cyan]Segment #{chunk_idx} (~{total_elapsed_sec // 60}m {total_elapsed_sec % 60}s)[/bold cyan]")
            
            # 1. Capture Audio Chunk
            audio_chunk = stream_engine.capture_audio_chunk(
                duration_sec=config.interval_seconds,
                chunk_idx=chunk_idx
            )

            # 2. Capture Screenshot
            screenshot_path = None
            if config.capture_screenshots:
                screenshot_path = stream_engine.capture_screenshot(screenshot_idx=chunk_idx)

            # 3. Transcribe Audio (0 API credits)
            t_res = transcriber.transcribe_audio_file(audio_chunk)
            transcript_text = t_res.get("text", "").strip()
            
            console.log(f"[italic dim]Transcript ({len(transcript_text)} chars): \"{transcript_text[:120]}...\"[/italic dim]")

            # 4. Analyze & Evaluate Highlight
            analysis = analyzer.analyze_chunk(
                current_transcript=transcript_text,
                recent_history=recent_history,
                timestamp_sec=total_elapsed_sec
            )

            # 5. Publish if highlight detected
            if analysis.get("is_highlight") and analysis.get("tweet"):
                tweet = analysis["tweet"]
                console.log(f"[bold magenta]Highlight Detected:[/bold magenta] {analysis.get('reason', '')}")
                publisher.publish(
                    tweet_text=tweet,
                    screenshot_path=screenshot_path,
                    metadata=analysis
                )
                recent_history.append(analysis.get("key_takeaway") or tweet)
            else:
                console.log(f"[dim]No critical highlight in segment #{chunk_idx} ({analysis.get('reason', 'Skipped')})[/dim]")

            total_elapsed_sec += config.interval_seconds

    except KeyboardInterrupt:
        console.log("\n[bold yellow]Monitoring stopped by user. StreamPulse shutting down clean.[/bold yellow]")


def main():
    parser = argparse.ArgumentParser(
        prog="streampulse",
        description="StreamPulse: Real-Time YouTube Live & Premiere to X (Twitter) AI Agent"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Run command
    run_parser = subparsers.add_parser("run", help="Start monitoring a YouTube stream/premiere")
    run_parser.add_argument("url", type=str, help="YouTube Live / Premiere URL")
    run_parser.add_argument("--interval", "-i", type=int, default=180, help="Interval in seconds (default: 180)")
    run_parser.add_argument("--whisper-model", "-w", type=str, default="base", help="Whisper model: tiny, base, small (default: base)")
    run_parser.add_argument("--lang", "-l", type=str, default=None, help="Language code (e.g. de, en, auto)")
    run_parser.add_argument("--provider", "-p", type=str, default="gemini", choices=["gemini", "openai", "groq", "ollama"], help="LLM provider")
    run_parser.add_argument("--llm-model", "-m", type=str, default="gemini-1.5-flash", help="LLM model name")
    run_parser.add_argument("--dry-run", action="store_true", help="Simulate posting without calling X API")
    run_parser.add_argument("--no-screenshots", action="store_true", help="Disable screenshot capture")
    run_parser.add_argument("--topic", "-t", type=str, default=None, help="Specific event topic or title")
    run_parser.add_argument("--tone", type=str, default=None, help="Desired post tone")
    run_parser.add_argument("--webhook", type=str, default=None, help="Discord/Slack webhook URL")

    # Version command
    subparsers.add_parser("version", help="Show StreamPulse version")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "version":
        console.print("[bold cyan]StreamPulse v1.0.0[/bold cyan] - Built by DeepMind / Antigravity")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
