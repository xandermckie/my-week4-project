"""Tests for Pomodoro intro popup dismissal and per-account persistence."""

import os
import tempfile

import pytest
from cryptography.fernet import Fernet

os.environ.setdefault("FERNET_KEY", Fernet.generate_key().decode())
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-api-key")

from app import create_app
from app.auth.helpers import hash_password
from app.storage import load_user, save_user


@pytest.fixture
def app_client(monkeypatch):
    """Create a Flask test client with isolated data directories."""
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
    monkeypatch.setenv("FERNET_KEY", Fernet.generate_key().decode())

    with tempfile.TemporaryDirectory() as tmp:
        users_dir = os.path.join(tmp, "users")
        sessions_dir = os.path.join(tmp, "sessions")
        avatars_dir = os.path.join(tmp, "avatars")
        cache_dir = os.path.join(tmp, "cache")
        os.makedirs(users_dir)
        os.makedirs(sessions_dir)
        os.makedirs(avatars_dir)
        os.makedirs(cache_dir)

        app = create_app()
        app.config.update(
            TESTING=True,
            USERS_DIR=users_dir,
            SESSIONS_DIR=sessions_dir,
            AVATARS_DIR=avatars_dir,
            CACHE_DIR=cache_dir,
        )

        with app.test_client() as client:
            yield app, client


def _register_user(app, email: str, password: str = "password123") -> None:
    """Save a minimal user record for testing."""
    with app.app_context():
        save_user(email, {
            "email": email,
            "password_hash": hash_password(password),
            "target_exam_date": None,
            "username": "",
            "agreed_to_terms_at": "2026-01-01T00:00:00+00:00",
            "birth_year_verified": True,
        })


def test_context_shows_not_dismissed_for_new_user(app_client):
    """Logged-in users without the flag see pomodoroIntroDismissed as false."""
    app, client = app_client
    email = "pomodoro@example.com"
    _register_user(app, email)

    with client.session_transaction() as sess:
        sess["email"] = email

    response = client.get("/")
    assert response.status_code == 200
    assert b"pomodoroIntroDismissed: false" in response.data


def test_dismiss_endpoint_sets_user_field(app_client):
    """POST dismiss persists pomodoro_intro_dismissed_at on the user record."""
    app, client = app_client
    email = "dismiss@example.com"
    _register_user(app, email)

    with client.session_transaction() as sess:
        sess["email"] = email

    response = client.post("/profile/pomodoro-intro/dismiss")
    assert response.status_code == 200
    assert response.get_json() == {"ok": True}

    with app.app_context():
        user = load_user(email)
    assert user.get("pomodoro_intro_dismissed_at")


def test_dismiss_endpoint_is_idempotent(app_client):
    """A second dismiss request still succeeds without changing the timestamp."""
    app, client = app_client
    email = "idempotent@example.com"
    _register_user(app, email)

    with client.session_transaction() as sess:
        sess["email"] = email

    client.post("/profile/pomodoro-intro/dismiss")
    with app.app_context():
        user_after_first = load_user(email)
    first_ts = user_after_first["pomodoro_intro_dismissed_at"]

    response = client.post("/profile/pomodoro-intro/dismiss")
    assert response.status_code == 200
    assert response.get_json() == {"ok": True}

    with app.app_context():
        user_after_second = load_user(email)
    assert user_after_second["pomodoro_intro_dismissed_at"] == first_ts


def test_context_shows_dismissed_after_save(app_client):
    """Template flag is true once the user record has been dismissed."""
    app, client = app_client
    email = "done@example.com"
    _register_user(app, email)

    with client.session_transaction() as sess:
        sess["email"] = email

    client.post("/profile/pomodoro-intro/dismiss")
    response = client.get("/")
    assert response.status_code == 200
    assert b"pomodoroIntroDismissed: true" in response.data


def test_dismiss_requires_login(app_client):
    """Unauthenticated users are redirected to login."""
    app, client = app_client
    response = client.post("/profile/pomodoro-intro/dismiss")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]
