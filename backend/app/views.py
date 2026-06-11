import os

import requests
from flask import Blueprint, jsonify, request, session

from .letterboxd import LetterboxdIntegrationError, build_letterboxd_slots
from .logic import build_result

views_bp = Blueprint("views", __name__)


@views_bp.get("/health")
def health():
    return jsonify({"ok": True})


@views_bp.get("/api/me")
def api_me():
    user_session = session.get("lastfm")
    if not user_session:
        return jsonify({"authenticated": False}), 401

    return jsonify({
        "authenticated": True,
        "user": user_session,
    })


@views_bp.get("/api/result")
def api_result():
    user_session = session.get("lastfm")
    if not user_session:
        return jsonify({"error": "Not authenticated"}), 401

    payload = build_result(user_session["name"])
    return jsonify(payload)


@views_bp.get("/api/integrations/letterboxd")
def api_letterboxd():
    username = request.args.get("username", "").strip()
    if not username:
        username = os.getenv("LETTERBOXD_USERNAME", "").strip()
    if not username:
        return jsonify({
            "error": "Pass ?username=... or configure LETTERBOXD_USERNAME"
        }), 400

    try:
        limit = int(request.args.get("limit", "24"))
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400

    language = request.args.get("language", "en-US").strip() or "en-US"

    try:
        return jsonify(build_letterboxd_slots(username, limit, language))
    except LetterboxdIntegrationError as exc:
        return jsonify({"error": str(exc)}), 400
    except requests.RequestException as exc:
        return jsonify({
            "error": "Could not load the Letterboxd RSS feed",
            "details": str(exc),
        }), 502
