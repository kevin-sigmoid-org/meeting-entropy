# Privacy Policy — meeting-entropy

**Version 1.0** — Last updated: 2026-04-06

Copyright (c) 2026 Julien Mer — kevin-sigmoid-org

---

## TL;DR

meeting-entropy collects **nothing**. Sends **nothing**. Stores **nothing** (unless you explicitly ask it to).

Kevin Sigmoid built this tool with one principle: your audio stays on your machine. Period.

---

## 1. Data We Collect

**By default: absolutely nothing.**

meeting-entropy processes audio from your microphone in real-time, entirely on your local machine. No data is collected, stored, transmitted, or retained after the application closes.

---

## 2. Optional Data Storage

If — and **only if** — you use the `--export` flag, meeting-entropy will save a session report to the path you specify. This file contains:

- Session duration
- Detected buzzword hits (word, category, weight, timestamp)
- Silence events (duration and timestamp)
- Transcribed text segments
- Entropy and email scores

These files are stored **locally** at the path you choose. By default, exports go to `~/.meeting-entropy/logs/`.

**We never create these files without your explicit request.**

---

## 3. Audio Processing

- Audio is captured from your default microphone via PyAudio
- Audio is transcribed locally using [faster-whisper](https://github.com/SYSTRAN/faster-whisper), an offline speech-to-text model
- **Audio is never recorded to disk**
- **Audio is never transmitted over the network**
- **Audio buffers are discarded immediately after transcription**
- The Whisper model runs 100% offline after initial download

---

## 4. Network Activity

meeting-entropy makes **zero** network calls during operation. None. Ever.

The only network activity occurs once, on first use, when the Whisper model is downloaded to `~/.meeting-entropy/models/`. After that, the model is cached locally and never re-downloaded.

**During a meeting session, there is absolutely no network activity.** You can verify this with any network monitor. Kevin encourages healthy paranoia.

---

## 5. Consent Management

On first launch, meeting-entropy asks for your explicit consent before doing anything. Your consent is stored in `~/.meeting-entropy/consent.json` with:

- Consent status (boolean)
- Timestamp (ISO 8601)
- Version of the consent prompt
- SHA256 hash of this Privacy Policy at the time of consent

If this Privacy Policy is updated (SHA256 hash changes), you will be asked to re-consent. This is how consent should work.

---

## 6. Right to Erasure

You can delete all meeting-entropy data at any time:

```bash
meeting-entropy --revoke-consent
```

This removes the entire `~/.meeting-entropy/` directory, including:
- Consent file
- Downloaded models
- Any exported session logs

After revocation, it's as if meeting-entropy was never installed. No traces. No breadcrumbs. No "we'll keep your data for 30 days just in case."

You can also manually delete `~/.meeting-entropy/` at any time. We won't stop you. We won't even know.

---

## 7. What We Will Never Do

- Send audio to any external server
- Send transcriptions to any external server
- Store data without explicit user consent
- Identify individual speakers
- Enable employee surveillance
- Provide a "stealth" or hidden listening mode
- Generate automated HR reports
- Sell, share, or monetize any data
- Phone home, ping analytics, or track usage
- Pretend that "continued use implies consent"

---

## 8. Third-Party Dependencies

- **faster-whisper**: Runs locally. No API calls.
- **PyAudio**: Local audio capture only.
- **Rich**: Terminal rendering. No network activity.
- **No analytics, telemetry, or tracking libraries are included.**

---

## 9. GDPR / RGPD Compliance

meeting-entropy is designed to be GDPR-compliant by default:

- **Lawful basis**: Explicit consent (Article 6(1)(a))
- **Data minimization**: No data collected by default
- **Purpose limitation**: Audio processed only for buzzword detection
- **Storage limitation**: No storage unless explicitly requested
- **Right to erasure**: `--revoke-consent` deletes everything
- **Transparency**: This document. You're reading it. That's more than most apps offer.

---

## 10. Integrity Verification

The SHA256 hash of this file is computed at the time of consent and stored in `~/.meeting-entropy/consent.json`. If this file is modified, meeting-entropy will detect the change and re-ask for consent.

This ensures you always know what you agreed to.

---

## 11. Contact

For privacy questions or GDPR requests:

- **GitHub Issues**: [kevin-sigmoid-org/meeting-entropy](https://github.com/kevin-sigmoid-org/meeting-entropy/issues)
- **Email**: Open an issue. Kevin checks GitHub more than email.

---

## 12. Changes to This Policy

Any changes to this policy will:
1. Update the version number
2. Change the SHA256 hash
3. Trigger a re-consent prompt on next launch
4. Be documented in the repository commit history

We don't sneak changes past you. That would be the kind of behavior this tool was built to detect.

---

*This privacy policy was written by a human who believes privacy policies should be readable.*
*If you actually read this far, Kevin is impressed. Most people don't even read the consent prompt.*
