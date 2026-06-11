"""Generate a personalized LSAT study plan using Claude."""

import logging
import os

import anthropic

logger = logging.getLogger(__name__)

# Dedicated timeout for plan generation: longer read window than the default
# chat client (25 s) because Sonnet produces a full 8-week markdown plan.
_PLAN_TIMEOUT = anthropic.Timeout(connect=5.0, read=120.0, write=10.0, pool=5.0)

_plan_client: anthropic.Anthropic | None = None


def _get_plan_client() -> anthropic.Anthropic:
    """Return a shared Anthropic client configured for long-running plan requests."""
    global _plan_client
    if _plan_client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY environment variable is not set.")
        _plan_client = anthropic.Anthropic(api_key=api_key, timeout=_PLAN_TIMEOUT)
    return _plan_client


def generate_study_plan(weak_areas: list[tuple[str, int]], target_date: str | None) -> str:
    """Call Claude to produce a week-by-week study plan.

    Args:
        weak_areas: Ranked list of (question_type, error_count) tuples.
        target_date: The student's exam date string (e.g. "2025-09-13"), or None.

    Returns:
        A markdown-formatted study plan string, or a user-friendly fallback message on error.
    """
    area_text = (
        "\n".join(f"- {qtype} ({count} errors)" for qtype, count in weak_areas)
        if weak_areas
        else "No specific weak areas identified yet."
    )
    date_text = f"Target exam date: {target_date}" if target_date else "No exam date set."

    prompt = (
        f"Create a focused LSAT study plan for a student with these details:\n\n"
        f"{date_text}\n\nWeak areas:\n{area_text}\n\n"
        "Produce a week-by-week plan (up to 8 weeks) with specific daily focus areas, "
        "practice targets, and review checkpoints. For each week include: a theme, "
        "Monday–Sunday daily tasks (30–90 min each), a mid-week check-in goal, and a "
        "weekend review exercise. Format as markdown with week headers."
    )

    try:
        client = _get_plan_client()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except anthropic.APITimeoutError:
        logger.exception("Claude API timeout in generate_study_plan")
        return "Plan generation timed out. Please try again — it sometimes takes a moment for longer plans."
    except anthropic.APIConnectionError:
        logger.exception("Claude API connection error in generate_study_plan")
        return "Could not reach the tutoring service. Please check your connection and try again."
    except anthropic.RateLimitError:
        logger.exception("Claude API rate limit error in generate_study_plan")
        return "The service is busy right now. Please wait a moment and try generating your plan again."
    except anthropic.AuthenticationError:
        logger.exception("Claude API authentication error in generate_study_plan")
        return "Study plan generation is unavailable. Please contact support."
    except anthropic.APIError:
        logger.exception("Unexpected Claude API error in generate_study_plan")
        return "Could not generate your study plan. Please try again in a few minutes."
