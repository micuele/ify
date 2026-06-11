import unittest
from unittest.mock import patch

from backend.app.letterboxd import (
    LetterboxdIntegrationError,
    build_letterboxd_slots,
    normalize_username,
    parse_letterboxd_feed,
)

RSS = """<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"
  xmlns:letterboxd="https://letterboxd.com"
  xmlns:tmdb="https://themoviedb.org">
  <channel>
    <item>
      <title>Perfect Days, 2023 - rating</title>
      <link>https://letterboxd.com/example/film/perfect-days-2023/</link>
      <guid>letterboxd-watch-123</guid>
      <pubDate>Tue, 10 Jun 2025 12:00:00 +0000</pubDate>
      <letterboxd:watchedDate>2025-06-09</letterboxd:watchedDate>
      <letterboxd:rewatch>Yes</letterboxd:rewatch>
      <letterboxd:filmTitle>Perfect Days</letterboxd:filmTitle>
      <letterboxd:filmYear>2023</letterboxd:filmYear>
      <letterboxd:memberRating>4.5</letterboxd:memberRating>
      <letterboxd:memberLike>Yes</letterboxd:memberLike>
      <tmdb:movieId>976893</tmdb:movieId>
      <description><![CDATA[<p><img src="https://example.com/poster.jpg"/></p>]]></description>
    </item>
    <item>
      <title>A list that should be ignored</title>
      <link>https://letterboxd.com/example/list/test/</link>
    </item>
  </channel>
</rss>
"""


class LetterboxdTests(unittest.TestCase):
    def test_parse_feed_keeps_only_film_entries(self):
        films = parse_letterboxd_feed(RSS)

        self.assertEqual(len(films), 1)
        self.assertEqual(films[0]["title"], "Perfect Days")
        self.assertEqual(films[0]["tmdb_id"], 976893)
        self.assertEqual(films[0]["rating"], 4.5)
        self.assertTrue(films[0]["liked"])
        self.assertTrue(films[0]["rewatch"])
        self.assertEqual(
            films[0]["letterboxd_poster_url"],
            "https://example.com/poster.jpg",
        )

    def test_username_validation_blocks_paths(self):
        self.assertEqual(normalize_username("@valid_user"), "valid_user")
        with self.assertRaises(LetterboxdIntegrationError):
            normalize_username("../../feed")

    @patch("backend.app.letterboxd.get_tmdb_movie")
    @patch("backend.app.letterboxd.fetch_letterboxd_feed", return_value=RSS)
    def test_builds_stable_padded_slots(self, _feed, tmdb_movie):
        tmdb_movie.return_value = {
            "status": "matched",
            "match_method": "id",
            "movie": {
                "id": 976893,
                "title": "Perfect Days",
                "overview": "A quiet and contemplative life in Tokyo.",
                "genres": [{"id": 18, "name": "Drama"}],
                "original_language": "ja",
            },
        }

        result = build_letterboxd_slots("example", limit=3)

        self.assertEqual(result["slot_count"], 3)
        self.assertEqual(result["film_count"], 1)
        self.assertEqual(result["slots"][0]["key"], "film-01")
        self.assertEqual(result["slots"][0]["data"]["tmdb"]["movie"]["id"], 976893)
        self.assertEqual(result["slots"][2]["image_key"], "film-03")
        self.assertIsNone(result["slots"][2]["data"])
        self.assertIn("selected_output", result)
        self.assertIn(result["selected_output"]["slot"], range(1, 25))


if __name__ == "__main__":
    unittest.main()
