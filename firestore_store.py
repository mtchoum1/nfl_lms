"""Firebase Admin SDK + Firestore client (lazy init)."""

from __future__ import annotations

import os

import firebase_admin
from firebase_admin import credentials, firestore

USERS_COLLECTION = "users"
LEAGUES_COLLECTION = "leagues"


def _project_id() -> str:
    return os.getenv("FIREBASE_PROJECT_ID", "nfl-lms")


def ensure_firebase_app() -> None:
    """Initialize the default Firebase app once (idempotent)."""
    if firebase_admin._apps:
        return
    project_id = _project_id()
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path and os.path.isfile(cred_path):
        cred = credentials.Certificate(cred_path)
    else:
        cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {"projectId": project_id})


def get_firestore_client():
    """Return a Firestore client; call :func:`ensure_firebase_app` first."""
    ensure_firebase_app()
    return firestore.client()
