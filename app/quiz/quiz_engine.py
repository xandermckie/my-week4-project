"""Quiz mode engine — selects questions, checks answers, records results."""

import json
import os
import random

_QUESTIONS: list[dict] | None = None


def _load_questions() -> list[dict]:
    """Load and cache the question bank from the JSON file."""
    global _QUESTIONS
    if _QUESTIONS is None:
        path = os.path.join(os.path.dirname(__file__), "..", "static", "questions.json")
        path = os.path.normpath(path)
        with open(path, encoding="utf-8") as f:
            _QUESTIONS = json.load(f)
    return _QUESTIONS


def get_question(question_type: str | None = None) -> dict:
    """Select a quiz question, optionally filtered by type.

    Args:
        question_type: If provided, only return questions of this type.

    Returns:
        A question dict with keys: type, stimulus, question, choices, correct, explanation.
    """
    pool = _load_questions()
    if question_type:
        filtered = [q for q in pool if q["type"] == question_type]
        pool = filtered if filtered else pool
    return random.choice(pool)


def check_answer(question: dict, submitted: str) -> dict:
    """Evaluate a submitted answer choice against the correct answer.

    Args:
        question: The question dict as returned by get_question().
        submitted: The letter choice submitted by the student (e.g. "A").

    Returns:
        A dict with keys: is_correct (bool), correct (str), explanation (str), submitted (str).
    """
    is_correct = submitted.upper() == question["correct"]
    return {
        "is_correct": is_correct,
        "correct": question["correct"],
        "explanation": question["explanation"],
        "submitted": submitted.upper(),
    }
