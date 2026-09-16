"""
Utility functions for StreamPulse
"""

import re
from datetime import datetime
from rich.console import Console

console = Console()


def get_timestamp_str() -> str:
    """Return formatted timestamp string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate_tweet_length(text: str) -> int:
    """
    Calculate tweet character count respecting Twitter's URL wrapping rule.
    Any URL in a tweet takes up 23 characters.
    """
    url_pattern = r"https?://\S+"
    # Replace all URLs with a 23-char placeholder
    normalized_text = re.sub(url_pattern, "x" * 23, text)
    return len(normalized_text)


def fit_tweet_length(text: str, max_chars: int = 280) -> str:
    """Ensure the text fits within the max length, trimming neatly if needed."""
    if calculate_tweet_length(text) <= max_chars:
        return text

    # Trim by words
    words = text.split()
    while words and calculate_tweet_length(" ".join(words) + "…") > max_chars:
        words.pop()

    return " ".join(words) + "…"
