from __future__ import annotations

import csv
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from statistics import mean
from typing import Any

import requests

LASTFM_API_ROOT = "https://ws.audioscrobbler.com/2.0/"


class LastfmLogicError(Exception):
    pass


def lastfm_get(params: dict[str, str]) -> dict[str, Any]:
    api_key = os.getenv("LASTFM_API_KEY", "")
    if not api_key:
        raise LastfmLogicError("Missing LASTFM_API_KEY")

    merged = {**params, "api_key": api_key, "format": "json"}
    response = requests.get(LASTFM_API_ROOT, params=merged, timeout=20)
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise LastfmLogicError(data.get("message", "Last.fm API error"))

    return data


@lru_cache(maxsize=256)
def get_artist_tags(artist_name: str) -> list[str]:
    if not artist_name:
        return []

    data = lastfm_get({
        "method": "artist.getTopTags",
        "artist": artist_name,
        "autocorrect": "1",
    })
    tags = data.get("toptags", {}).get("tag", [])
    if isinstance(tags, dict):
        tags = [tags]
    return [tag.get("name", "").strip().lower() for tag in tags[:10] if tag.get("name")]


@lru_cache(maxsize=256)
def get_track_tags(artist_name: str, track_name: str) -> list[str]:
    if not artist_name or not track_name:
        return []

    data = lastfm_get({
        "method": "track.getTopTags",
        "artist": artist_name,
        "track": track_name,
        "autocorrect": "1",
    })
    tags = data.get("toptags", {}).get("tag", [])
    if isinstance(tags, dict):
        tags = [tags]
    return [tag.get("name", "").strip().lower() for tag in tags[:8] if tag.get("name")]


@lru_cache(maxsize=128)
def get_top_artists(username: str, period: str = "7day", limit: int = 30) -> list[dict[str, Any]]:
    data = lastfm_get({
        "method": "user.getTopArtists",
        "user": username,
        "period": period,
        "limit": str(limit),
    })
    artists = data.get("topartists", {}).get("artist", [])
    if isinstance(artists, dict):
        artists = [artists]
    return artists


@lru_cache(maxsize=128)
def get_top_tracks(username: str, period: str = "7day", limit: int = 30) -> list[dict[str, Any]]:
    data = lastfm_get({
        "method": "user.getTopTracks",
        "user": username,
        "period": period,
        "limit": str(limit),
    })
    tracks = data.get("toptracks", {}).get("track", [])
    if isinstance(tracks, dict):
        tracks = [tracks]
    return tracks


@lru_cache(maxsize=128)
def get_top_albums(username: str, period: str = "7day", limit: int = 20) -> list[dict[str, Any]]:
    data = lastfm_get({
        "method": "user.getTopAlbums",
        "user": username,
        "period": period,
        "limit": str(limit),
    })
    albums = data.get("topalbums", {}).get("album", [])
    if isinstance(artists:=albums, dict):
        albums = [albums]
    return albums


def fetch_recent_tracks(username: str, days: int = 7) -> list[dict[str, Any]]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    tracks: list[dict[str, Any]] = []
    page = 1

    while True:
        data = lastfm_get({
            "method": "user.getRecentTracks",
            "user": username,
            "limit": "200",
            "page": str(page),
            "from": str(int(start.timestamp())),
            "to": str(int(end.timestamp())),
            "extended": "1",
        })

        recenttracks = data.get("recenttracks", {})
        page_tracks = recenttracks.get("track", [])
        attr = recenttracks.get("@attr", {})

        if isinstance(page_tracks, dict):
            page_tracks = [page_tracks]
        if not page_tracks:
            break

        tracks.extend(page_tracks)

        total_pages = int(attr.get("totalPages", "1") or 1)
        if page >= total_pages:
            break
        page += 1

    return tracks


def normalize_recent_track(track: dict[str, Any]) -> dict[str, Any]:
    artist = track.get("artist", {})
    album = track.get("album", {})
    date = track.get("date", {})
    uts = date.get("uts")
    nowplaying = track.get("@attr", {}).get("nowplaying") == "true"

    return {
        "name": track.get("name", "Unknown"),
        "artist": artist.get("name") or artist.get("#text", "Unknown"),
        "artist_mbid": artist.get("mbid", ""),
        "album": album.get("#text", ""),
        "album_mbid": album.get("mbid", ""),
        "loved": str(track.get("loved", "0")) == "1",
        "nowplaying": nowplaying,
        "uts": int(uts) if uts and str(uts).isdigit() else None,
        "image": track.get("image", []),
        "url": track.get("url", ""),
    }


def summarize_recent_tracks(recent_tracks: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = [normalize_recent_track(track) for track in recent_tracks]
    finished_scrobbles = [t for t in normalized if t["uts"] is not None]

    artist_counts = Counter(t["artist"] for t in finished_scrobbles if t["artist"])
    track_counts = Counter((t["artist"], t["name"]) for t in finished_scrobbles if t["artist"] and t["name"])
    album_counts = Counter((t["artist"], t["album"]) for t in finished_scrobbles if t["artist"] and t["album"])

    loved_count = sum(1 for t in normalized if t["loved"])
    nowplaying = next((t for t in normalized if t["nowplaying"]), None)

    timestamps = sorted(t["uts"] for t in finished_scrobbles if t["uts"] is not None)
    hours = [datetime.fromtimestamp(ts, tz=timezone.utc).hour for ts in timestamps]
    weekdays = [datetime.fromtimestamp(ts, tz=timezone.utc).weekday() for ts in timestamps]

    gaps = [b - a for a, b in zip(timestamps, timestamps[1:])]
    short_gaps = [gap for gap in gaps if gap <= 60 * 90]

    morning = sum(1 for h in hours if 5 <= h < 12)
    afternoon = sum(1 for h in hours if 12 <= h < 18)
    evening = sum(1 for h in hours if 18 <= h < 24)
    night = sum(1 for h in hours if 0 <= h < 5)

    return {
        "total_scrobbles": len(finished_scrobbles),
        "unique_artists": len(artist_counts),
        "unique_tracks": len(track_counts),
        "unique_albums": len(album_counts),
        "artist_diversity_ratio": round(len(artist_counts) / len(finished_scrobbles), 4) if finished_scrobbles else 0,
        "track_repeat_ratio": round(1 - (len(track_counts) / len(finished_scrobbles)), 4) if finished_scrobbles else 0,
        "top_artists": [{"artist": name, "count": count} for name, count in artist_counts.most_common(10)],
        "top_tracks": [{"artist": artist, "track": track, "count": count} for (artist, track), count in track_counts.most_common(10)],
        "top_albums": [{"artist": artist, "album": album, "count": count} for (artist, album), count in album_counts.most_common(10)],
        "loved_count": loved_count,
        "currently_playing": nowplaying,
        "hour_distribution": {
            "night": night,
            "morning": morning,
            "afternoon": afternoon,
            "evening": evening,
        },
        "weekday_distribution": dict(Counter(weekdays)),
        "average_gap_seconds": round(mean(short_gaps), 2) if short_gaps else None,
        "session_like_gap_count": len(short_gaps),
        "first_scrobble_uts": timestamps[0] if timestamps else None,
        "last_scrobble_uts": timestamps[-1] if timestamps else None,
        "raw_recent_tracks": normalized,
    }


def collect_tag_signals(top_artists: list[dict[str, Any]], top_tracks: list[dict[str, Any]]) -> dict[str, Any]:
    artist_tag_counts: Counter[str] = Counter()
    track_tag_counts: Counter[str] = Counter()

    for artist in top_artists[:10]:
        name = artist.get("name", "")
        for tag in get_artist_tags(name):
            artist_tag_counts[tag] += 1

    for track in top_tracks[:10]:
        artist_name = track.get("artist", {}).get("name") or track.get("artist", {}).get("#text") or ""
        track_name = track.get("name", "")
        for tag in get_track_tags(artist_name, track_name):
            track_tag_counts[tag] += 1

    combined = artist_tag_counts + track_tag_counts

    return {
        "artist_top_tags": artist_tag_counts.most_common(20),
        "track_top_tags": track_tag_counts.most_common(20),
        "combined_top_tags": combined.most_common(30),
    }


def collect_all_datapoints(username: str) -> dict[str, Any]:
    user_info = lastfm_get({"method": "user.getInfo", "user": username}).get("user", {})
    recent_tracks = fetch_recent_tracks(username, days=7)
    recent_summary = summarize_recent_tracks(recent_tracks)

    top_artists_7d = get_top_artists(username, period="7day", limit=30)
    top_tracks_7d = get_top_tracks(username, period="7day", limit=30)
    top_albums_7d = get_top_albums(username, period="7day", limit=20)

    top_artists_1m = get_top_artists(username, period="1month", limit=20)
    top_tracks_1m = get_top_tracks(username, period="1month", limit=20)

    tag_signals = collect_tag_signals(top_artists_7d, top_tracks_7d)

    return {
        "user": {
            "name": user_info.get("name", username),
            "realname": user_info.get("realname", ""),
            "country": user_info.get("country", ""),
            "playcount": int(user_info.get("playcount", "0") or 0),
            "artist_count": int(user_info.get("artist_count", "0") or 0),
            "track_count": int(user_info.get("track_count", "0") or 0),
            "album_count": int(user_info.get("album_count", "0") or 0),
            "subscriber": user_info.get("subscriber", "0"),
            "registered": user_info.get("registered", {}),
            "image": user_info.get("image", []),
            "url": user_info.get("url", ""),
        },
        "weekly_recent_summary": recent_summary,
        "weekly_top_artists": top_artists_7d,
        "weekly_top_tracks": top_tracks_7d,
        "weekly_top_albums": top_albums_7d,
        "monthly_top_artists": top_artists_1m,
        "monthly_top_tracks": top_tracks_1m,
        "tag_signals": tag_signals,
    }


def build_result(username: str) -> dict[str, Any]:
    datapoints = collect_all_datapoints(username)
    
    # Extract the user's generated tag weights for the week
    weekly_tags_summary = datapoints["tag_signals"].get("combined_top_tags", [])
    
    # Rebuild a Counter structure based on Last.fm data
    tag_counts = Counter()
    for tag, score in weekly_tags_summary:
        tag_counts[tag.lower()] = score

    # Load emoji profile rules from CSV file
    emoji_profiles = {}
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    csv_filename = os.path.join(BASE_DIR, "emoji_profiles.csv")
    
    # Fallback variables
    winner_emoji = "😡" 
    max_score = 0
    emoji_scores = {}

    if os.path.exists(csv_filename):
        try:
            with open(csv_filename, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    emoji = (row.get("emoji") or "").strip()
                    if not emoji:
                        continue

                    profiletags = [
                        (value or "").strip().lower()
                        for key, value in row.items()
                        if key and key.lower().startswith("tag") and (value or "").strip()
                    ]
                    # FIXED: Added underscore
                    emoji_profiles[emoji] = profiletags

            # FIXED: Added underscores to emoji_scores, tag_counts, and emoji_profiles
            emoji_scores = {
                emoji: sum(tag_counts[tag] for tag in profiletags if tag in tag_counts)
                for emoji, profiletags in emoji_profiles.items()
            }

            if emoji_scores:
                top_emoji = max(emoji_scores, key=emoji_scores.get)
                # FIXED: Added underscores to max_score and winner_emoji
                max_score = emoji_scores[top_emoji]
                if max_score > 0:
                    winner_emoji = top_emoji

        except Exception as e:
            print(f"Error reading emoji CSV: {e}")

    total_scrobbles = datapoints["weekly_recent_summary"]["total_scrobbles"]

    # FIXED: Updated print variables to match their initialized names
    print("tag_counts:", tag_counts)
    print("profiles:", emoji_profiles)
    print("scores:", emoji_scores)
    print("max_score:", max_score)

    return {
        "user": datapoints["user"],
        "selected_output": {
            "key": "total_scrobbles_last_7_days",
            "label": "Total scrobbles in the last 7 days",
            "value": total_scrobbles,
            "emoji": winner_emoji,
            "match_score": max_score
        },
        "datapoints": datapoints,
    }