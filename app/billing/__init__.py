"""Billing blueprint — free/pro tier management and mock payment."""

from flask import Blueprint

billing_bp = Blueprint("billing", __name__)

from app.billing import routes  # noqa: E402, F401
