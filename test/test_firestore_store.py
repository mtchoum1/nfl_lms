"""Firebase Admin credential loading."""

from __future__ import annotations

import json
from unittest.mock import patch

from firebase_admin import credentials

from firestore_store import _load_credentials


def test_load_credentials_uses_certificate_for_service_account(tmp_path, monkeypatch):
    sa_path = tmp_path / "sa.json"
    sa_path.write_text(
        json.dumps({"type": "service_account", "project_id": "nfl-lms"}),
        encoding="utf-8",
    )
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(sa_path))

    with patch.object(credentials, "Certificate", return_value="cert") as cert:
        assert _load_credentials() == "cert"
    cert.assert_called_once_with(str(sa_path))


def test_load_credentials_uses_application_default_for_user_adc(tmp_path, monkeypatch):
    adc_path = tmp_path / "adc.json"
    adc_path.write_text(json.dumps({"type": "authorized_user", "client_id": "x"}), encoding="utf-8")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(adc_path))

    with patch.object(credentials, "ApplicationDefault", return_value="adc") as adc:
        assert _load_credentials() == "adc"
    adc.assert_called_once()
