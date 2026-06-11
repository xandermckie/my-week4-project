"""Outbound email helpers — all mail goes through Flask-Mail with HTML templates."""

import logging
from datetime import date, datetime, timezone

from flask import current_app, render_template
from flask_mail import Message

from app.extensions import mail

logger = logging.getLogger(__name__)

_APP_URL = "http://127.0.0.1:5000"  # Override in production via APP_URL env var


def _app_url() -> str:
    """Return the public base URL for links inside emails."""
    import os
    return os.environ.get("APP_URL", _APP_URL).rstrip("/")


def _is_mail_ready() -> bool:
    """Return True if Flask-Mail is configured and enabled."""
    return bool(
        current_app.config.get("MAIL_ENABLED")
        and current_app.config.get("MAIL_PASSWORD")
    )


def _send(subject: str, recipients: list[str], html: str, text: str) -> bool:
    """Send a single email, returning True on success.

    Args:
        subject: Email subject line.
        recipients: List of recipient addresses.
        html: HTML body.
        text: Plain-text fallback body.

    Returns:
        True if sent successfully, False on any error.
    """
    try:
        msg = Message(subject=subject, recipients=recipients, html=html, body=text)
        mail.send(msg)
        logger.info("Email sent to %s — %s", recipients, subject)
        return True
    except Exception as exc:
        logger.warning("Email failed to %s: %s", recipients, exc)
        return False


# ── Public senders ────────────────────────────────────────────────────────────

def send_welcome(user_email: str, display_name: str) -> bool:
    """Send the welcome email to a newly registered user.

    Args:
        user_email: Recipient address.
        display_name: The user's chosen display name or email prefix.

    Returns:
        True if sent, False if mail is not configured or sending failed.
    """
    if not _is_mail_ready():
        return False

    ctx = {"display_name": display_name, "app_url": _app_url()}
    html = render_template("email/welcome.html", **ctx)
    text = (
        f"Welcome to Ratio, {display_name}!\n\n"
        "Your account is ready. Head to the app to start your first quiz and "
        "earn XP toward your first streak.\n\n"
        f"Open the app: {_app_url()}/chat\n\n"
        "— The Ratio Team\n"
    )
    return _send(
        subject="Welcome to Ratio — your LSAT tutor is ready",
        recipients=[user_email],
        html=html,
        text=text,
    )


def send_weekly_digest(
    user_email: str,
    display_name: str,
    *,
    questions_this_week: int,
    correct_this_week: int,
    xp_earned: int,
    streak_count: int,
    top_weak_area: str | None,
    upcoming_exam_date: str | None,
) -> bool:
    """Send the weekly progress digest email.

    Args:
        user_email: Recipient address.
        display_name: The user's display name.
        questions_this_week: Total questions answered in the past 7 days.
        correct_this_week: Number answered correctly.
        xp_earned: XP gained this week.
        streak_count: Current streak length.
        top_weak_area: The question type with the most errors, or None.
        upcoming_exam_date: ISO date string of the target exam, or None.

    Returns:
        True if sent, False otherwise.
    """
    if not _is_mail_ready():
        return False

    accuracy_pct = (
        round(correct_this_week / questions_this_week * 100)
        if questions_this_week > 0
        else 0
    )

    days_until_exam: int | None = None
    if upcoming_exam_date:
        try:
            exam_dt = date.fromisoformat(upcoming_exam_date)
            days_until_exam = (exam_dt - date.today()).days
        except ValueError:
            pass

    weak_area_tips = {
        "Weaken": "Find a premise that, if true, makes the conclusion less likely — look for alternative causes or counter-evidence.",
        "Strengthen": "Look for a premise that closes the gap between evidence and conclusion, ruling out alternatives.",
        "Assumption": "Find the unstated premise the argument needs to be valid. Ask: what must be true for the evidence to support the conclusion?",
        "Flaw": "Name the logical error: false dilemma, ad hominem, correlation/causation, necessary vs. sufficient conditions.",
        "Inference": "Only pick what must be true given the premises. Avoid anything that goes beyond what is stated.",
        "Main Point": "The conclusion is the claim the argument is trying to prove — it's what all the other sentences support.",
        "Parallel Reasoning": "Strip the argument to its skeleton (All A are B; X is A; therefore…) and match the structure, not the content.",
        "Principle": "Identify the general rule the argument relies on and pick the answer that, if established, would justify the specific decision.",
        "Resolve": "Find the fact that explains both sides of the apparent contradiction — usually a third variable neither side considered.",
        "Reading Comprehension": "Re-read the specific lines the question references and eliminate answers that go beyond what the passage says.",
        "Method of Reasoning": "Describe what the argument actually does, step by step — is it drawing an analogy, applying a principle, or citing evidence?",
        "Point at Issue": "The correct answer must be something both speakers would take opposing positions on if asked directly.",
    }
    weak_area_tip = weak_area_tips.get(
        top_weak_area or "", "Focus on reading the stimulus carefully before looking at answer choices."
    )

    week_of = date.today().strftime("%B %d, %Y")

    ctx = {
        "display_name": display_name,
        "app_url": _app_url(),
        "week_of": week_of,
        "questions_this_week": questions_this_week,
        "accuracy_pct": accuracy_pct,
        "xp_earned": xp_earned,
        "streak_count": streak_count,
        "top_weak_area": top_weak_area,
        "weak_area_tip": weak_area_tip,
        "upcoming_exam_date": upcoming_exam_date,
        "days_until_exam": days_until_exam,
    }
    html = render_template("email/weekly_digest.html", **ctx)
    text = (
        f"Hi {display_name},\n\n"
        f"Your week: {questions_this_week} questions, {accuracy_pct}% accuracy, {xp_earned} XP earned.\n"
        f"Streak: {streak_count} days.\n"
        f"Focus area: {top_weak_area or 'keep up the variety'}.\n\n"
        f"Open the app: {_app_url()}/quiz\n\n"
        "— The Ratio Team\n"
    )
    return _send(
        subject=f"Your Ratio weekly update — week of {week_of}",
        recipients=[user_email],
        html=html,
        text=text,
    )


def send_streak_warning(user_email: str, display_name: str, streak_count: int) -> bool:
    """Send a streak-at-risk warning when a user hasn't studied yet today.

    Args:
        user_email: Recipient address.
        display_name: The user's display name.
        streak_count: Current streak length about to be lost.

    Returns:
        True if sent, False otherwise.
    """
    if not _is_mail_ready():
        return False

    ctx = {"display_name": display_name, "app_url": _app_url(), "streak_count": streak_count}
    html = render_template("email/streak_warning.html", **ctx)
    text = (
        f"Hi {display_name},\n\n"
        f"Your {streak_count}-day streak is at risk! Answer one question before midnight "
        f"to keep it alive.\n\n"
        f"Go to the quiz: {_app_url()}/quiz\n\n"
        "— The Ratio Team\n"
    )
    return _send(
        subject=f"Don't lose your {streak_count}-day streak, {display_name}!",
        recipients=[user_email],
        html=html,
        text=text,
    )


def send_upgrade_confirmation(user_email: str, display_name: str) -> bool:
    """Send a Pro upgrade confirmation email.

    Args:
        user_email: Recipient address.
        display_name: The user's display name.

    Returns:
        True if sent, False otherwise.
    """
    if not _is_mail_ready():
        return False

    ctx = {"display_name": display_name, "app_url": _app_url()}
    html = render_template("email/upgrade_confirmation.html", **ctx)
    text = (
        f"Hi {display_name},\n\n"
        "Your Ratio Pro subscription is active. All features are now unlocked.\n\n"
        f"Start a session: {_app_url()}/chat\n\n"
        "— The Ratio Team\n"
    )
    return _send(
        subject="You're on Ratio Pro — welcome to the full experience",
        recipients=[user_email],
        html=html,
        text=text,
    )


def send_plan_email(user_email: str, plan_text: str, exam_date: str | None) -> bool:
    """Send the user's generated study plan to their email address.

    Args:
        user_email: Recipient address.
        plan_text: The raw markdown plan text.
        exam_date: ISO date string for the target exam, or None.

    Returns:
        True if sent, False otherwise.
    """
    if not _is_mail_ready():
        return False

    exam_line = f"Target exam date: {exam_date}" if exam_date else "No exam date set."
    body = (
        "Hi,\n\n"
        "Here is your personalized LSAT study plan from Ratio.\n\n"
        f"{exam_line}\n\n"
        "--- YOUR STUDY PLAN ---\n\n"
        f"{plan_text}\n\n"
        "---\n\n"
        "Log in at any time to view your plan, track weak areas, and practice.\n\n"
        "Good luck on your LSAT!\n"
        "The Ratio Team\n"
    )
    return _send(
        subject="Your Ratio LSAT Study Plan",
        recipients=[user_email],
        html=f"<pre style='font-family:monospace;white-space:pre-wrap'>{plan_text}</pre>",
        text=body,
    )


def send_daily_reminder(user_email: str, focus_area: str, exam_date: str | None) -> bool:
    """Send a short daily study nudge email.

    Args:
        user_email: Recipient address.
        focus_area: Today's recommended focus question type.
        exam_date: ISO date string for the target exam, or None.

    Returns:
        True if sent, False otherwise.
    """
    if not _is_mail_ready():
        return False

    exam_line = (
        f"Your exam is on {exam_date}. Keep pushing!"
        if exam_date
        else "Set your exam date in Study Plan to get a personalized schedule."
    )
    text = (
        f"Today's focus: {focus_area}\n\n"
        f"{exam_line}\n\n"
        f"Head to the quiz: {_app_url()}/quiz\n\n"
        "Good luck today!\n— The Ratio Team\n"
    )
    return _send(
        subject=f"Ratio: Today focus on {focus_area}",
        recipients=[user_email],
        html=text.replace("\n", "<br>"),
        text=text,
    )
