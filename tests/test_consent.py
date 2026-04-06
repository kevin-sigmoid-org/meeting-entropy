"""Tests for the RGPD/GDPR consent module.

Because privacy is not optional — and neither is testing it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from meeting_entropy import consent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect CONSENT_DIR and CONSENT_FILE to a temp directory.

    This ensures tests never touch the real ~/.meeting-entropy.
    """
    fake_consent_dir = tmp_path / ".meeting-entropy"
    fake_consent_file = fake_consent_dir / "consent.json"

    monkeypatch.setattr(consent, "CONSENT_DIR", fake_consent_dir)
    monkeypatch.setattr(consent, "CONSENT_FILE", fake_consent_file)

    return tmp_path


@pytest.fixture()
def fake_privacy_md(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a fake PRIVACY.md for hash testing."""
    privacy_path = tmp_path / "PRIVACY.md"
    privacy_path.write_text("Privacy policy v1.0\n", encoding="utf-8")
    monkeypatch.setattr(consent, "PRIVACY_MD", privacy_path)
    return privacy_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestConsentRefusal:
    """Si l'utilisateur refuse le consentement, RIEN ne doit etre cree.

    Pas un fichier. Pas un log. Pas une trace. RGPD oblige. Kevin aussi.
    """

    def test_consent_refusal_leaves_no_trace(
        self,
        fake_home: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "n")
        result = consent.ask_for_consent_like_a_civilized_tool()

        assert result is False
        consent_dir = fake_home / ".meeting-entropy"
        assert not consent_dir.exists(), "Refusing consent must not create any directory"

    def test_consent_refusal_with_no(
        self,
        fake_home: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "no")
        result = consent.ask_for_consent_like_a_civilized_tool()

        assert result is False
        assert not (fake_home / ".meeting-entropy").exists()

    def test_consent_refusal_with_ctrl_c(
        self,
        fake_home: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def raise_keyboard_interrupt(_: str) -> str:
            raise KeyboardInterrupt

        monkeypatch.setattr("builtins.input", raise_keyboard_interrupt)
        result = consent.ask_for_consent_like_a_civilized_tool()

        assert result is False
        assert not (fake_home / ".meeting-entropy").exists()


class TestConsentAcceptance:
    """Test that accepting consent creates consent.json."""

    def test_consent_acceptance_creates_file(
        self,
        fake_home: Path,
        fake_privacy_md: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "y")
        result = consent.ask_for_consent_like_a_civilized_tool()

        assert result is True
        consent_file = fake_home / ".meeting-entropy" / "consent.json"
        assert consent_file.exists()

        data = json.loads(consent_file.read_text(encoding="utf-8"))
        assert data["consented"] is True
        assert "timestamp" in data
        assert "sha256_policy" in data
        assert data["version"] == "1.0"

    def test_consent_acceptance_with_oui(
        self,
        fake_home: Path,
        fake_privacy_md: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr("builtins.input", lambda _: "oui")
        result = consent.ask_for_consent_like_a_civilized_tool()
        assert result is True

    def test_consent_acceptance_with_empty_string(
        self,
        fake_home: Path,
        fake_privacy_md: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Empty input defaults to acceptance."""
        monkeypatch.setattr("builtins.input", lambda _: "")
        result = consent.ask_for_consent_like_a_civilized_tool()
        assert result is True


class TestCheckConsent:
    """Test that check_consent returns True when valid consent.json exists."""

    def test_check_consent_with_valid_file(
        self,
        fake_home: Path,
        fake_privacy_md: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # First, give consent
        monkeypatch.setattr("builtins.input", lambda _: "y")
        consent.ask_for_consent_like_a_civilized_tool()

        # Then, check it
        assert consent.check_consent() is True

    def test_check_consent_without_file(
        self,
        fake_home: Path,
    ) -> None:
        assert consent.check_consent() is False

    def test_check_consent_with_corrupt_file(
        self,
        fake_home: Path,
    ) -> None:
        consent_dir = fake_home / ".meeting-entropy"
        consent_dir.mkdir(parents=True)
        consent_file = consent_dir / "consent.json"
        consent_file.write_text("NOT VALID JSON {{{{", encoding="utf-8")

        assert consent.check_consent() is False

    def test_check_consent_with_revoked(
        self,
        fake_home: Path,
    ) -> None:
        consent_dir = fake_home / ".meeting-entropy"
        consent_dir.mkdir(parents=True)
        consent_file = consent_dir / "consent.json"
        consent_file.write_text(
            json.dumps({"consented": False}),
            encoding="utf-8",
        )

        assert consent.check_consent() is False


class TestRevokeConsent:
    """Test that revoke_consent removes the .meeting-entropy directory."""

    def test_revoke_consent_removes_everything(
        self,
        fake_home: Path,
        fake_privacy_md: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Give consent first
        monkeypatch.setattr("builtins.input", lambda _: "y")
        consent.ask_for_consent_like_a_civilized_tool()

        consent_dir = fake_home / ".meeting-entropy"
        assert consent_dir.exists()

        # Now revoke
        consent.revoke_consent()
        assert not consent_dir.exists()

    def test_revoke_consent_when_nothing_exists(
        self,
        fake_home: Path,
    ) -> None:
        """Revoking consent when no data exists should not raise."""
        consent.revoke_consent()  # Should not raise


class TestPrivacyHashReconsent:
    """Test that changing PRIVACY.md invalidates consent."""

    def test_privacy_hash_change_triggers_reconsent(
        self,
        fake_home: Path,
        fake_privacy_md: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Give consent with current PRIVACY.md
        monkeypatch.setattr("builtins.input", lambda _: "y")
        consent.ask_for_consent_like_a_civilized_tool()

        assert consent.check_consent() is True

        # Now change PRIVACY.md
        fake_privacy_md.write_text(
            "Privacy policy v2.0 — Kevin added a new clause.\n",
            encoding="utf-8",
        )

        # Consent should now be invalid
        assert consent.check_consent() is False
