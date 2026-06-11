import unittest
from collections import Counter

from backend.app.vibes import VIBE_CATEGORIES, category_catalog, classify_vibe


class VibeClassifierTests(unittest.TestCase):
    def test_catalog_has_24_unique_image_slots(self):
        catalog = category_catalog()

        self.assertEqual(len(VIBE_CATEGORIES), 24)
        self.assertEqual(len({item["key"] for item in catalog}), 24)
        self.assertEqual(
            [item["image_key"] for item in catalog],
            [f"{slot:02d}" for slot in range(1, 25)],
        )

    def test_standard_tmdb_genres_have_one_primary_owner(self):
        standard_genres = {
            "action", "adventure", "animation", "comedy", "crime",
            "documentary", "drama", "family", "fantasy", "history",
            "horror", "music", "mystery", "romance", "science fiction",
            "tv movie", "thriller", "war", "western",
        }
        owners = Counter(
            genre
            for category in VIBE_CATEGORIES
            for genre in category.film_genres
        )

        self.assertTrue(standard_genres.issubset(owners))
        self.assertTrue(all(owners[genre] == 1 for genre in standard_genres))

    def test_heavy_music_maps_to_heavy_impact(self):
        result = classify_vibe(
            music_tags=Counter({"death metal": 8, "thrash metal": 5}),
            seed="heavy",
        )

        self.assertEqual(result["key"], "metal-action-adrenaline")
        self.assertEqual(result["image_key"], "15")

    def test_dream_music_maps_to_ethereal_dream(self):
        result = classify_vibe(
            music_tags=Counter({"dream pop": 9, "shoegaze": 6}),
            seed="dream",
        )

        self.assertEqual(result["key"], "fantasy-dream-pop")

    def test_horror_film_maps_to_gothic_dread(self):
        result = classify_vibe(
            film_genres=Counter({"Horror": 5}),
            seed="horror",
        )

        self.assertEqual(result["key"], "horror-gothic-dark")

    def test_science_fiction_maps_to_neon_future(self):
        result = classify_vibe(
            film_genres=Counter({"Science Fiction": 4}),
            seed="future",
        )

        self.assertEqual(result["key"], "sci-fi-electronic-future")


if __name__ == "__main__":
    unittest.main()
