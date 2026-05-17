import hashlib
import os
from urllib.parse import urlencode

import requests
from flask import Blueprint, jsonify, redirect, request, session

LASTFM_API_ROOT = "https://ws.audioscrobbler.com/2.0/"
LASTFM_AUTH_ROOT = "https://www.last.fm/api/auth/"

auth_bp = Blueprint("auth", __name__)


def sign_lastfm(params: dict[str, str]) -> str:
    api_secret = os.getenv("LASTFM_API_SECRET", "")
    filtered = {k: v for k, v in params.items() if k != "format" and v is not None}
    raw = "".join(f"{k}{filtered[k]}" for k in sorted(filtered.keys())) + api_secret
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


@auth_bp.get("/auth/lastfm")
def auth_lastfm():
    api_key = os.getenv("LASTFM_API_KEY", "")
    callback_url = os.getenv("LASTFM_CALLBACK_URL", "http://127.0.0.1:5000/auth/lastfm/callback")

    if not api_key:
        return jsonify({"error": "Missing LASTFM_API_KEY"}), 500

    query = urlencode({
        "api_key": api_key,
        "cb": callback_url,
    })
    return redirect(f"{LASTFM_AUTH_ROOT}?{query}")


@auth_bp.get("/auth/lastfm/callback")
def auth_lastfm_callback():
    api_key = os.getenv("LASTFM_API_KEY", "")
    token = request.args.get("token")
    frontend_url = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")

    if not token:
        return jsonify({"error": "Missing token"}), 400
    if not api_key or not os.getenv("LASTFM_API_SECRET"):
        return jsonify({"error": "Missing Last.fm API credentials"}), 500

    params = {
        "method": "auth.getSession",
        "api_key": api_key,
        "token": token,
    }
    params["api_sig"] = sign_lastfm(params)
    params["format"] = "json"

    response = requests.get(LASTFM_API_ROOT, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    if "session" not in data:
        return jsonify({"error": "Failed to create session", "details": data}), 400

    session["lastfm"] = {
        "name": data["session"]["name"],
        "key": data["session"]["key"],
        "subscriber": data["session"].get("subscriber", 0),
    }

    return redirect(f"{frontend_url}/?logged_in=1")


@auth_bp.post("/logout")
def logout():
    session.pop("lastfm", None)
    return jsonify({"ok": True})
