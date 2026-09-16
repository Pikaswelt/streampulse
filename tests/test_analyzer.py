"""
Unit tests for StreamPulse
"""

import unittest
from streampulse.utils import calculate_tweet_length, fit_tweet_length
from streampulse.analyzer import ContentAnalyzer


class TestStreamPulse(unittest.TestCase):
    def test_tweet_length_calculation(self):
        # Plain text
        self.assertEqual(calculate_tweet_length("Hello World"), 11)
        # Text with URL (counts as 23 characters)
        url_text = "Check out https://youtube.com/watch?v=123456789 for details"
        self.assertEqual(calculate_tweet_length(url_text), 10 + 23 + 12)

    def test_fit_tweet_length(self):
        long_text = "A " * 200
        fitted = fit_tweet_length(long_text, max_chars=100)
        self.assertLessEqual(calculate_tweet_length(fitted), 100)
        self.assertTrue(fitted.endswith("…"))

    def test_heuristic_analyzer_detection(self):
        analyzer = ContentAnalyzer(provider="heuristic")
        transcript = (
            "Willkommen alle zusammen. Heute stellen wir ein komplett neues Feature vor! "
            "Unsere AI Engine ist ab sofort 10x schneller und open source verfügbar für alle Entwickler weltweit."
        )
        res = analyzer.analyze_chunk(transcript, recent_history=[], timestamp_sec=120)
        self.assertTrue(res["is_highlight"])
        self.assertIn("tweet", res)
        self.assertLessEqual(calculate_tweet_length(res["tweet"]), 280)


if __name__ == "__main__":
    unittest.main()
