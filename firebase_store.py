"""Firebase Admin SDK + Realtime Database (lazy init)."""

from __future__ import annotations

import os
from pathlib import Path

import firebase_admin
from firebase_admin import auth, credentials, db

DEFAULT_DATABASE_URL = "https://nfl-lms-default-rtdb.firebaseio.com"
USERS_PATH = "users"
LEAGUES_PATH = "leagues"

_dotenv_loaded = False


def _load_dotenv_once() -> None:
    global _dotenv_loaded
    if _dotenv_loaded:
        return
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
    _dotenv_loaded = True


def _project_id() -> str:
    return os.getenv("FIREBASE_PROJECT_ID", "nfl-lms")


def _database_url() -> str:
    return os.getenv("FIREBASE_DATABASE_URL", DEFAULT_DATABASE_URL).strip()


def _load_credentials():
    """Service account JSON uses Certificate; user ADC files use ApplicationDefault."""
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if cred_path and os.path.isfile(cred_path):
        import json

        with open(cred_path, encoding="utf-8") as f:
            info = json.load(f)
        if info.get("type") == "service_account":
            return credentials.Certificate(cred_path)
    return credentials.ApplicationDefault()


def ensure_firebase_app() -> None:
    """Initialize the default Firebase app once (idempotent)."""
    _load_dotenv_once()
    if firebase_admin._apps:
        return
    project_id = _project_id()
    cred = _load_credentials()
    firebase_admin.initialize_app(
        cred,
        {
            "projectId": project_id,
            "databaseURL": _database_url(),
        },
    )


def get_database():
    """Return the Realtime Database module; call :func:`ensure_firebase_app` first."""
    ensure_firebase_app()
    return db


def get_auth():
    """Return Firebase Auth (Admin SDK); call :func:`ensure_firebase_app` first."""
    ensure_firebase_app()
    return auth
