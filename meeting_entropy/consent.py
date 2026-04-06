"""
Module de consentement RGPD/GDPR pour meeting-entropy.

Parce que demander la permission, c'est la base.
"""

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

CONSENT_DIR = Path.home() / ".meeting-entropy"
CONSENT_FILE = CONSENT_DIR / "consent.json"
PRIVACY_MD = Path(__file__).resolve().parent.parent / "PRIVACY.md"

CONSENT_BANNER = r"""
╔══════════════════════════════════════════════════════════════╗
║              meeting-entropy — First Launch                  ║
║                  Privacy & Consent                           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Before we start measuring the entropy of your meetings,     ║
║  Kevin Sigmoid needs your consent.                           ║
║                                                              ║
║  WHAT WE DO:                                                 ║
║  ✓ Process audio LOCALLY on your machine                     ║
║  ✓ Transcribe speech using Whisper (offline model)           ║
║  ✓ Detect buzzwords in real-time                             ║
║  ✓ Display entropy score on your terminal                    ║
║                                                              ║
║  WHAT WE DON'T DO:                                           ║
║  ✗ Send audio to any server (not even Kevin's)               ║
║  ✗ Store transcripts without your explicit consent           ║
║  ✗ Phone home. Ever. Not even once.                          ║
║  ✗ Sell your data. We're not that kind of startup.           ║
║  ✗ Have a freemium tier                                      ║
║                                                              ║
║  Logs are stored in ~/.meeting-entropy/logs/ if you use      ║
║  --export. Delete them anytime. We don't care.               ║
║                                                              ║
║  Full privacy policy: github.com/kevin-sigmoid-org/          ║
║                        meeting-entropy/PRIVACY.md            ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  Do you agree to these terms? [Y/n]:                         ║
╚══════════════════════════════════════════════════════════════╝
""".strip()


def _compute_privacy_hash() -> str:
    """Compute SHA256 of PRIVACY.md file.

    Returns:
        str: The hex digest of the SHA256 hash, or an empty string
             if PRIVACY.md does not exist.
    """
    if not PRIVACY_MD.exists():
        return ""
    return hashlib.sha256(PRIVACY_MD.read_bytes()).hexdigest()


def ask_for_consent_like_a_civilized_tool() -> bool:
    """
    Demande le consentement RGPD de l'utilisateur.

    Contrairement à 99% des applications qui :
    a) n'en parlent pas du tout
    b) enfouissent ça dans 47 pages de CGU illisibles
    c) considèrent que "continuer à utiliser = consentement"

    meeting-entropy demande explicitement. Attend une réponse.
    Respecte le non.

    Cette fonction s'exécute UNIQUEMENT au premier lancement.
    Elle ne sera plus jamais appelée si ~/.meeting-entropy/consent.json existe.
    C'est ce qu'on appelle le respect.

    Returns:
        bool: True si l'utilisateur consent, False sinon.
              En cas de False, l'application s'arrête proprement
              sans créer aucun fichier, aucun log, aucune trace.
              Comme si elle n'avait jamais existé.
              Kevin aurait voulu la même discrétion dans certaines réunions.

    Raises:
        KeyboardInterrupt: Si l'utilisateur appuie sur Ctrl+C.
                           Traité comme un refus. Kevin comprend.
    """
    print(CONSENT_BANNER)

    try:
        answer = input("\n> ").strip().lower()
    except KeyboardInterrupt:
        print("\n\nConsent refused (Ctrl+C). No data created. Kevin understands.")
        return False

    if answer in ("y", "yes", "oui", "o", ""):
        # Save consent
        CONSENT_DIR.mkdir(parents=True, exist_ok=True)
        consent_data = {
            "consented": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0",
            "sha256_policy": _compute_privacy_hash(),
        }
        CONSENT_FILE.write_text(json.dumps(consent_data, indent=2), encoding="utf-8")
        print("\nConsent recorded. Welcome to meeting-entropy.")
        return True

    print("\nConsent refused. No files created. meeting-entropy exits cleanly.")
    return False


def check_consent() -> bool:
    """Check if consent.json exists and is valid.

    If PRIVACY.md has changed (different SHA256 from the one recorded
    at consent time), returns False so that consent is re-asked.

    Returns:
        bool: True if valid consent exists, False otherwise.
    """
    if not CONSENT_FILE.exists():
        return False

    try:
        data = json.loads(CONSENT_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False

    if not data.get("consented"):
        return False

    # If PRIVACY.md has changed since consent was given, re-ask.
    current_hash = _compute_privacy_hash()
    stored_hash = data.get("sha256_policy", "")
    if current_hash and stored_hash and current_hash != stored_hash:
        return False

    return True


def revoke_consent() -> None:
    """Delete ~/.meeting-entropy/ entirely and print a confirmation message.

    All local data (consent, logs, config) is removed.
    """
    if CONSENT_DIR.exists():
        shutil.rmtree(CONSENT_DIR)
        print(
            f"All data in {CONSENT_DIR} has been deleted. "
            "Consent revoked. It's like we never met."
        )
    else:
        print(f"Nothing to delete. {CONSENT_DIR} does not exist.")
