from __future__ import annotations

import os
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from email.utils import parsedate_to_datetime
from functools import lru_cache
from html.parser import HTMLParser
from typing import Any
from xml.etree import ElementTree

import requests

from .vibes import classify_vibe, text_signals

LETTERBOXD_ROOT = "https://letterboxd.com"
LETTERBOXD_NAMESPACE = "https://letterboxd.com"
TMDB_NAMESPACE = "https://themoviedb.org"
TMDB_API_ROOT = "https://api.themoviedb.org/3"
TMDB_IMAGE_ROOT = "https://image.tmdb.org/t/p"
MAX_FILMS = 24
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{1,30}$")
TMDB_GENRE_SPECIFICITY = {
    "drama": 0.35,
    "comedy": 0.65,
    "action": 0.8,
    "adventure": 0.8,
    "animation": 1.0,
    "crime": 0.8,
    "documentary": 1.0,
    "family": 0.8,
    "fantasy": 0.9,
    "history": 0.9,
    "horror": 1.1,
    "music": 1.0,
    "mystery": 1.0,
    "romance": 0.9,
    "science fiction": 1.1,
    "tv movie": 0.5,
    "thriller": 0.8,
    "war": 1.0,
    "western": 1.1,
}


class LetterboxdIntegrationError(Exception):
    pass


class _FirstImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.src: str | None = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag.lower() != "img" or self.src:
            return
        self.src = dict(attrs).get("src")


def _text(
    element: ElementTree.Element,
    path: str,
    namespaces: dict[str, str] | None = None,
) -> str:
    value = element.findtext(path, namespaces=namespaces)
    return value.strip() if value else ""


def _optional_int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _iso_datetime(value: str) -> str | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).isoformat()
    except (TypeError, ValueError):
        return None


def _poster_from_description(description: str) -> str | None:
    parser = _FirstImageParser()
    parser.feed(description)
    return parser.src


def normalize_username(username: str) -> str:
    normalized = username.strip().lstrip("@")
    if not USERNAME_PATTERN.fullmatch(normalized):
        raise LetterboxdIntegrationError("Invalid Letterboxd username")
    return normalized


def fetch_letterboxd_feed(username: str) -> str:
    normalized = normalize_username(username)
    response = requests.get(
        f"{LETTERBOXD_ROOT}/{normalized}/rss/",
        headers={"User-Agent": "ify/1.0 (Letterboxd RSS integration)"},
        timeout=20,
    )
    if response.status_code == 404:
        raise LetterboxdIntegrationError("Letterboxd profile not found or not public")
    response.raise_for_status()
    return response.text


def parse_letterboxd_feed(xml: str, limit: int = MAX_FILMS) -> list[dict[str, Any]]:
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError as exc:
        raise LetterboxdIntegrationError("Letterboxd returned an invalid RSS feed") from exc

    namespace = {
        "letterboxd": LETTERBOXD_NAMESPACE,
        "tmdb": TMDB_NAMESPACE,
    }
    films: list[dict[str, Any]] = []

    for item in root.findall("./channel/item"):
        title = _text(item, "letterboxd:filmTitle", namespace)
        if not title:
            continue

        description = _text(item, "description")
        films.append({
            "title": title,
            "year": _optional_int(_text(item, "letterboxd:filmYear", namespace)),
            "watched_date": _text(item, "letterboxd:watchedDate", namespace) or None,
            "published_at": _iso_datetime(_text(item, "pubDate")),
            "rating": _optional_float(_text(item, "letterboxd:memberRating", namespace)),
            "liked": _text(item, "letterboxd:memberLike", namespace).lower() == "yes",
            "rewatch": _text(item, "letterboxd:rewatch", namespace).lower() == "yes",
            "letterboxd_url": _text(item, "link"),
            "letterboxd_guid": _text(item, "guid"),
            "letterboxd_poster_url": _poster_from_description(description),
            "tmdb_id": _optional_int(_text(item, "tmdb:movieId", namespace)),
        })
        if len(films) >= limit:
            break

    return films


def _tmdb_credentials() -> tuple[dict[str, str], dict[str, str]]:
    access_token = os.getenv("TMDB_ACCESS_TOKEN", "").strip()
    api_key = os.getenv("TMDB_API_KEY", "").strip()
    headers = {
        "accept": "application/json",
        "User-Agent": "ify/1.0",
    }
    params: dict[str, str] = {}

    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    elif api_key:
        params["api_key"] = api_key
    else:
        raise LetterboxdIntegrationError(
            "Missing TMDB_ACCESS_TOKEN or TMDB_API_KEY"
        )

    return headers, params


def _tmdb_get(path: str, params: dict[str, str] | None = None) -> dict[str, Any]:
    headers, auth_params = _tmdb_credentials()
    response = requests.get(
        f"{TMDB_API_ROOT}{path}",
        headers=headers,
        params={**auth_params, **(params or {})},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def _image_url(path: str | None, size: str) -> str | None:
    return f"{TMDB_IMAGE_ROOT}/{size}{path}" if path else None


def _normalize_tmdb_movie(movie: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": movie.get("id"),
        "title": movie.get("title"),
        "original_title": movie.get("original_title"),
        "overview": movie.get("overview"),
        "release_date": movie.get("release_date") or None,
        "runtime_minutes": movie.get("runtime"),
        "genres": [
            {"id": genre.get("id"), "name": genre.get("name")}
            for genre in movie.get("genres", [])
        ],
        "original_language": movie.get("original_language"),
        "popularity": movie.get("popularity"),
        "vote_average": movie.get("vote_average"),
        "vote_count": movie.get("vote_count"),
        "poster_path": movie.get("poster_path"),
        "poster_url": _image_url(movie.get("poster_path"), "w500"),
        "backdrop_path": movie.get("backdrop_path"),
        "backdrop_url": _image_url(movie.get("backdrop_path"), "w1280"),
        "tmdb_url": (
            f"https://www.themoviedb.org/movie/{movie['id']}"
            if movie.get("id")
            else None
        ),
    }


@lru_cache(maxsize=512)
def get_tmdb_movie(
    tmdb_id: int | None,
    title: str,
    year: int | None,
    language: str,
) -> dict[str, Any]:
    movie_id = tmdb_id
    match_method = "id"

    if movie_id is None:
        search_params = {
            "query": title,
            "include_adult": "false",
            "language": language,
        }
        if year:
            search_params["year"] = str(year)
        results = _tmdb_get("/search/movie", search_params).get("results", [])
        if not results:
            raise LetterboxdIntegrationError(f'TMDB match not found for "{title}"')
        movie_id = results[0].get("id")
        if not movie_id:
            raise LetterboxdIntegrationError(
                f'TMDB returned an invalid match for "{title}"'
            )
        match_method = "title_year"

    movie = _tmdb_get(f"/movie/{movie_id}", {"language": language})
    return {
        "status": "matched",
        "match_method": match_method,
        "movie": _normalize_tmdb_movie(movie),
    }


def _enrich_film(film: dict[str, Any], language: str) -> dict[str, Any]:
    try:
        tmdb = get_tmdb_movie(
            film["tmdb_id"],
            film["title"],
            film["year"],
            language,
        )
    except (LetterboxdIntegrationError, requests.RequestException) as exc:
        tmdb = {
            "status": "unavailable",
            "match_method": None,
            "movie": None,
            "error": str(exc),
        }
    return {**film, "tmdb": tmdb}


def classify_letterboxd_films(
    films: list[dict[str, Any]],
    username: str,
) -> dict[str, object]:
    genre_counts: Counter[str] = Counter()
    text_values: list[str] = []
    traits: Counter[str] = Counter()
    languages: set[str] = set()
    years: list[int] = []

    for film in films:
        rating = film.get("rating")
        preference_weight = 1.0
        if film.get("liked"):
            preference_weight += 0.75
        if isinstance(rating, (int, float)) and rating >= 4:
            preference_weight += 0.75
        elif isinstance(rating, (int, float)) and rating <= 2:
            preference_weight *= 0.5

        movie = film.get("tmdb", {}).get("movie") or {}
        for genre in movie.get("genres", []):
            name = genre.get("name")
            if name:
                specificity = TMDB_GENRE_SPECIFICITY.get(name.lower(), 1.0)
                genre_counts[name] += preference_weight * specificity

        text_values.extend([
            film.get("title", ""),
            movie.get("title", ""),
            movie.get("overview", ""),
        ])
        language = movie.get("original_language")
        if language:
            languages.add(language)
        year = film.get("year")
        if isinstance(year, int):
            years.append(year)
        if film.get("rewatch"):
            traits["rewatch"] += preference_weight

    current_year = datetime.now().year
    if years and sum(1 for year in years if year <= current_year - 25) / len(years) >= 0.4:
        traits["older_catalog"] = 1
    if len(languages) >= 5:
        traits["high_diversity"] = 1

    return classify_vibe(
        film_genres=genre_counts,
        text=text_signals(text_values),
        traits=traits,
        seed=f"letterboxd:{username}",
    )


def build_letterboxd_slots(
    username: str,
    limit: int = MAX_FILMS,
    language: str = "en-US",
) -> dict[str, Any]:
    normalized_username = normalize_username(username)
    bounded_limit = max(1, min(limit, MAX_FILMS))
    films = parse_letterboxd_feed(
        fetch_letterboxd_feed(normalized_username),
        bounded_limit,
    )

    with ThreadPoolExecutor(max_workers=min(6, len(films) or 1)) as executor:
        enriched_films = list(
            executor.map(lambda film: _enrich_film(film, language), films)
        )

    slots = []
    for index in range(bounded_limit):
        film = enriched_films[index] if index < len(enriched_films) else None
        slots.append({
            "slot": index + 1,
            "key": f"film-{index + 1:02d}",
            "image_key": f"film-{index + 1:02d}",
            "source": "letterboxd",
            "data": film,
        })

    return {
        "provider": "letterboxd",
        "username": normalized_username,
        "profile_url": f"{LETTERBOXD_ROOT}/{normalized_username}/",
        "generated_at": datetime.now().astimezone().isoformat(),
        "slot_count": bounded_limit,
        "film_count": len(enriched_films),
        "selected_output": classify_letterboxd_films(
            enriched_films,
            normalized_username,
        ),
        "slots": slots,
    }
