"""
Publisher & Live Feed Engine
Publishes live posts to X (Twitter), sends Webhook alerts,
and generates a real-time Markdown live feed with 1-click posting links.
"""

import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from rich.panel import Panel
from rich.text import Text
from streampulse.utils import console, get_timestamp_str

try:
    import tweepy
except ImportError:
    tweepy = None


class Publisher:
    def __init__(
        self,
        consumer_key: Optional[str] = None,
        consumer_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
        bearer_token: Optional[str] = None,
        discord_webhook_url: Optional[str] = None,
        live_feed_path: Optional[Path] = None,
        dry_run: bool = False
    ):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.bearer_token = bearer_token
        self.discord_webhook_url = discord_webhook_url
        self.live_feed_path = live_feed_path or Path("./output/live_feed.md")
        self.dry_run = dry_run

        self._twitter_client: Optional[Any] = None
        self._twitter_v1_api: Optional[Any] = None
        self._init_twitter()
        self._init_markdown_feed()

    def _init_twitter(self):
        """Initialize Tweepy v2 Client & v1 API for media uploads."""
        if not tweepy:
            return

        if self.consumer_key and self.consumer_secret and self.access_token and self.access_token_secret:
            try:
                # v2 Client for posting tweets
                self._twitter_client = tweepy.Client(
                    bearer_token=self.bearer_token,
                    consumer_key=self.consumer_key,
                    consumer_secret=self.consumer_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret
                )
                # v1.1 API needed for image upload
                auth = tweepy.OAuth1UserHandler(
                    self.consumer_key,
                    self.consumer_secret,
                    self.access_token,
                    self.access_token_secret
                )
                self._twitter_v1_api = tweepy.API(auth)
                console.log("[green]✓ Twitter/X API authenticated successfully.[/green]")
            except Exception as e:
                console.log(f"[yellow]Twitter/X auth warning: {e}[/yellow]")

    def _init_markdown_feed(self):
        """Initialize Markdown Live Feed header if file does not exist."""
        if not self.live_feed_path.exists():
            self.live_feed_path.parent.mkdir(parents=True, exist_ok=True)
            header = f"""# 🔴 StreamPulse - Live Stream Feed
*Started: {get_timestamp_str()}*

Real-time highlights, AI-crafted X posts, and stream snapshots.

---
"""
            self.live_feed_path.write_text(header, encoding="utf-8")

    def publish(
        self,
        tweet_text: str,
        screenshot_path: Optional[Path] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main publish dispatcher.
        Outputs to console, updates Markdown feed, sends webhooks, and posts to X.
        """
        timestamp = get_timestamp_str()
        meta = metadata or {}
        post_url = None

        # 1. Console Display Card
        panel_content = Text()
        panel_content.append(f"{tweet_text}\n\n", style="bold white")
        panel_content.append(f"⏱ Timestamp: {timestamp} | Length: {len(tweet_text)} chars\n", style="dim cyan")
        if screenshot_path and screenshot_path.exists():
            panel_content.append(f"📸 Snapshot: {screenshot_path.name}\n", style="dim green")

        console.print(Panel(panel_content, title="[bold cyan]🚀 StreamPulse Generated Post[/bold cyan]", border_style="cyan"))

        # 2. X / Twitter API Posting
        if not self.dry_run and self._twitter_client:
            media_ids = []
            if screenshot_path and screenshot_path.exists() and self._twitter_v1_api:
                try:
                    media = self._twitter_v1_api.media_upload(filename=str(screenshot_path))
                    media_ids.append(media.media_id)
                    console.log(f"[green]✓ Uploaded media to Twitter (ID: {media.media_id})[/green]")
                except Exception as e:
                    console.log(f"[red]Failed to upload media to Twitter: {e}[/red]")

            try:
                kwargs = {"text": tweet_text}
                if media_ids:
                    kwargs["media_ids"] = media_ids
                resp = self._twitter_client.create_tweet(**kwargs)
                tweet_id = resp.data.get("id")
                post_url = f"https://x.com/i/status/{tweet_id}"
                console.log(f"[bold green]✓ Published to X:[/bold green] {post_url}")
            except Exception as e:
                console.log(f"[red]Error publishing tweet to X: {e}[/red]")
        elif self.dry_run:
            console.log("[dim italic yellow]--dry-run active: Skipped posting to X API.[/dim italic yellow]")

        # 3. Discord / Slack Webhook
        if self.discord_webhook_url:
            self._send_discord_webhook(tweet_text, screenshot_path, post_url)

        # 4. Append to Live Markdown Feed (With 1-Click Tweet Intent)
        self._append_to_markdown_feed(tweet_text, screenshot_path, timestamp, post_url)

        return {"published": bool(post_url), "url": post_url, "text": tweet_text}

    def _send_discord_webhook(self, text: str, screenshot_path: Optional[Path], post_url: Optional[str]):
        try:
            payload = {
                "content": f"**🔴 New Stream Highlight Post**\n{text}" + (f"\n🔗 [View on X]({post_url})" if post_url else "")
            }
            files = {}
            if screenshot_path and screenshot_path.exists():
                files = {"file": open(screenshot_path, "rb")}
            requests.post(self.discord_webhook_url, data=payload, files=files, timeout=10)
        except Exception as e:
            console.log(f"[dim yellow]Discord webhook failed: {e}[/dim yellow]")

    def _append_to_markdown_feed(
        self,
        tweet_text: str,
        screenshot_path: Optional[Path],
        timestamp: str,
        post_url: Optional[str]
    ):
        encoded_tweet = urllib.parse.quote(tweet_text)
        intent_url = f"https://twitter.com/intent/tweet?text={encoded_tweet}"

        rel_img_path = f"screenshots/{screenshot_path.name}" if screenshot_path else ""

        entry = f"""
### ⚡ Highlight at {timestamp}

> {tweet_text}

"""
        if screenshot_path and screenshot_path.exists():
            entry += f"![Stream Snapshot]({rel_img_path})\n\n"

        if post_url:
            entry += f"👉 **[Published on X]({post_url})**\n\n"
        else:
            entry += f"🚀 **[1-Click Post to X / Twitter]({intent_url})** *(Ready to publish)*\n\n"

        entry += "---\n"

        with open(self.live_feed_path, "a", encoding="utf-8") as f:
            f.write(entry)
