"""Chat blueprint routes — the main tutoring interface."""

import re

from flask import current_app, jsonify, redirect, render_template, request, session, url_for

from app.analysis.weak_area_detector import update_weak_areas
from app.auth.helpers import login_required
from app.chat import chat_bp
from app.chat.claude_client import call_claude
from app.chat.context_manager import maybe_compress
from app.chat.prompt_builder import build_messages
from app.extensions import limiter
from app.storage import load_session, save_session

_META_RE = re.compile(
    r"\nRATIO_META type=(\S+) result=(correct|incorrect|neutral)\s*$",
    re.IGNORECASE,
)


def _extract_meta(text: str) -> tuple[str, str | None, str | None]:
    """Strip the RATIO_META tracking line from the response and return its fields.

    Returns:
        (clean_text, question_type_or_None, result_or_None)
    """
    match = _META_RE.search(text)
    if not match:
        return text, None, None
    clean = text[: match.start()].rstrip()
    return clean, match.group(1), match.group(2).lower()


@chat_bp.route("/chat", methods=["GET"])
@login_required
def chat():
    """Render the main chat interface."""
    return render_template("chat/chat.html")


@chat_bp.route("/chat", methods=["POST"])
@login_required
@limiter.limit("20 per hour")
def send_message():
    """Accept a student's message, call Claude, and return the coaching response.

    Expects JSON body: {"message": "..."}
    Returns JSON: {"response": "..."}
    """
    data = request.get_json(silent=True)
    if not data or not data.get("message", "").strip():
        return jsonify({"error": "Message is required."}), 400

    email = session["email"]
    user_input = data["message"].strip().replace("\x00", "")
    if len(user_input) > 3000:
        return jsonify({"error": "Message too long (max 3,000 characters)."}), 400

    session_data = load_session(email)
    session_data = maybe_compress(
        session_data,
        threshold=current_app.config["CONTEXT_COMPRESSION_THRESHOLD"],
        turns_to_compress=current_app.config["CONTEXT_TURNS_TO_COMPRESS"],
    )

    messages, system = build_messages(
        user_input=user_input,
        turns=session_data.get("turns", []),
        summary=session_data.get("summary", ""),
        weak_areas=session_data.get("weak_areas", {}),
    )

    response_text = call_claude(
        messages=messages,
        system=system,
        cache_dir=current_app.config["CACHE_DIR"],
    )

    # Strip the hidden tracking tag and use it to update weak areas.
    clean_response, qtype, result = _extract_meta(response_text)
    if result == "incorrect" and qtype:
        session_data = update_weak_areas(
            session_data, user_input, was_correct=False, question_type=qtype
        )

    session_data.setdefault("turns", []).append({"role": "user", "content": user_input})
    session_data["turns"].append({"role": "assistant", "content": clean_response})
    save_session(email, session_data)

    return jsonify({"response": clean_response})


@chat_bp.route("/history")
@login_required
def history():
    """Return the current user's chat history as JSON."""
    email = session["email"]
    session_data = load_session(email)
    return jsonify({"turns": session_data.get("turns", [])})


@chat_bp.route("/clear-history", methods=["POST"])
@login_required
def clear_history():
    """Clear all session history for the current user."""
    email = session["email"]
    save_session(email, {"turns": [], "summary": "", "weak_areas": {}})
    return redirect(url_for("chat.chat"))
