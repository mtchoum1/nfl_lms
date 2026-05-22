"""E2E: user signup persists to Realtime Database."""

from unittest.mock import MagicMock, patch

import pytest

from firebase_store import USERS_PATH
from test.database_fake import InMemoryDatabase
from user import User

pytestmark = pytest.mark.e2e


@patch("firebase_store.get_auth")
@patch("firebase_store.get_database")
def test_user_signup_persists_to_database_e2e(mock_get_db, mock_get_auth, api_client):
    db = InMemoryDatabase()
    mock_get_db.return_value = db
    auth_module = MagicMock()
    record = MagicMock()
    record.uid = "e2e-user-uid"
    auth_module.create_user.return_value = record
    mock_get_auth.return_value = auth_module

    signup = api_client.post(
        "/api/v1/users",
        json={"name": "E2E User", "email": "e2e@example.com", "password": "secure-test-pass"},
    )
    assert signup.status_code == 201
    body = signup.json()
    assert body == {"id": "e2e-user-uid", "name": "E2E User", "email": "e2e@example.com"}

    assert db.get_node(f"{USERS_PATH}/e2e-user-uid") == {
        "id": "e2e-user-uid",
        "name": "E2E User",
        "email": "e2e@example.com",
    }

    fetched = api_client.get("/api/v1/users/e2e-user-uid")
    assert fetched.status_code == 200
    assert fetched.json() == body

    loaded = User.load_from_database("e2e-user-uid", db_module=db)
    assert loaded is not None
    assert loaded.get_name() == "E2E User"
    assert loaded.get_email() == "e2e@example.com"
