import unittest
from unittest.mock import patch

from backend.app.logic import build_result


class LastfmResultTests(unittest.TestCase):
    @patch("backend.app.logic.collect_all_datapoints")
    def test_returns_shared_vibe_image_without_emoji(self, collect):
        collect.return_value = {
            "user": {"name": "listener"},
            "weekly_recent_summary": {
                "total_scrobbles": 80,
                "artist_diversity_ratio": 0.3,
                "hour_distribution": {
                    "night": 10,
                    "morning": 20,
                    "afternoon": 30,
                    "evening": 20,
                },
            },
            "weekly_top_artists": [{"name": "Heavy Artist"}],
            "weekly_top_tracks": [{"name": "Heavy Track"}],
            "tag_signals": {
                "combined_top_tags": [
                    ("death metal", 10),
                    ("thrash metal", 7),
                ],
            },
        }

        result = build_result("listener")

        self.assertEqual(result["provider"], "lastfm")
        self.assertEqual(result["selected_output"]["image_key"], "15")
        self.assertEqual(result["selected_output"]["key"], "metal-action-adrenaline")
        self.assertNotIn("emoji", result["selected_output"])


if __name__ == "__main__":
    unittest.main()
