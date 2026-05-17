from flask import Blueprint, jsonify, session

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
