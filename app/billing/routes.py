"""Billing routes — upgrade page and mock payment processing."""

import logging

from flask import redirect, render_template, request, session, url_for

logger = logging.getLogger(__name__)

from app.billing import billing_bp
from app.storage import load_user, save_user

# Per-tier limits (enforced in chat and quiz routes via get_tier_limits())
TIER_LIMITS = {
    "free": {
        "chat_daily": 25,
        "quiz_daily": 50,
        "friends": True,
        "challenges": True,
        "leaderboard": True,
        "study_plan": True,
        "study_plan_edits": False,   # Free: 1 generation + 1 date correction
        "unlimited_quiz": False,
        "unlimited_chat": False,
    },
    "pro": {
        "chat_daily": 9999,
        "quiz_daily": 9999,
        "friends": True,
        "challenges": True,
        "leaderboard": True,
        "study_plan": True,
        "study_plan_edits": True,    # Pro: unlimited regenerations + edits
        "unlimited_quiz": True,
        "unlimited_chat": True,
    },
}


def get_tier_limits(user: dict) -> dict:
    """Return the feature limits for a user based on their tier.

    Args:
        user: The user dict loaded from storage.

    Returns:
        A dict of feature limits for the user's current tier.
    """
    tier = user.get("tier", "free")
    return TIER_LIMITS.get(tier, TIER_LIMITS["free"])


@billing_bp.route("/upgrade", methods=["GET", "POST"])
def upgrade():
    """Render the upgrade page and process mock payments."""
    email = session.get("email")
    if not email:
        return redirect(url_for("auth.login"))

    user = load_user(email)
    if user is None:
        return redirect(url_for("auth.login"))

    current_tier = user.get("tier", "free")
    success = False
    error = None

    if request.method == "POST":
        card_number = request.form.get("card_number", "").replace(" ", "")
        expiry = request.form.get("expiry", "").strip()
        cvv = request.form.get("cvv", "").strip()
        name = request.form.get("card_name", "").strip()

        # Mock validation — any 16-digit number, MM/YY expiry, 3-digit CVV
        if len(card_number) != 16 or not card_number.isdigit():
            error = "Please enter a valid 16-digit card number."
        elif len(cvv) not in (3, 4) or not cvv.isdigit():
            error = "Please enter a valid CVV."
        elif not expiry or len(expiry) != 5 or expiry[2] != "/":
            error = "Please enter expiry in MM/YY format."
        elif not name:
            error = "Please enter the name on your card."
        else:
            user["tier"] = "pro"
            save_user(email, user)
            success = True
            current_tier = "pro"
            # Best-effort upgrade confirmation email
            try:
                from app.email_service import send_upgrade_confirmation
                display_name = user.get("username") or email.split("@")[0]
                send_upgrade_confirmation(email, display_name)
            except Exception as exc:
                logger.warning("Upgrade confirmation email failed for %s: %s", email, exc)

    return render_template(
        "billing/upgrade.html",
        current_tier=current_tier,
        tier_limits=TIER_LIMITS,
        success=success,
        error=error,
    )


@billing_bp.route("/downgrade", methods=["POST"])
def downgrade():
    """Downgrade a Pro account to the Free tier."""
    email = session.get("email")
    if not email:
        return redirect(url_for("auth.login"))

    user = load_user(email)
    if user is not None:
        user["tier"] = "free"
        save_user(email, user)

    return redirect(url_for("billing.upgrade"))
