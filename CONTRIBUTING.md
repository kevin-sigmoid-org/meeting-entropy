# Contributing to meeting-entropy

First off: thank you for considering a contribution to the fight against corporate entropy. Kevin Sigmoid personally reviews every PR, usually between 2 AM and 4 AM, fueled by espresso and existential dread. Your patience is appreciated.

## Table of Contents

- [Adding Words to the Corpus](#adding-words-to-the-corpus)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Code Style](#code-style)
- [Testing](#testing)
- [License](#license)

## Adding Words to the Corpus

Corpus files live in the `corpus/` directory as YAML files, one per language (plus `universal.yaml` for language-agnostic terms). The format is straightforward:

```yaml
metadata:
  language: "fr"              # ISO 639-1 language code
  version: "1.0"
  curator: "Kevin Sigmoid"
  note: "A short, preferably sarcastic description."

categories:
  category_name:
    weight: 7                  # 1-10, how egregious this category is
    words:
      - "synergie"
      - "paradigme"
      - "aller de l'avant"     # Multi-word phrases are fine
    sarcasm_level: "MAXIMUM"   # One of: MODERATE, HIGH, CRITICAL, MAXIMUM
    note: "Optional editorial commentary. Kevin encourages honesty here."
```

### Guidelines for new words

- **Be specific.** "Good" is not a buzzword. "Let's leverage our core competencies going forward" absolutely is.
- **Multi-word phrases are welcome.** The detector matches substrings, so "circle back" will catch "let's circle back on that."
- **Pick an honest weight.** 1-3 for mild filler, 4-6 for standard corporate fog, 7-9 for weaponized vagueness, 10 for "synergy."
- **Sarcasm levels** are `MODERATE`, `HIGH`, `CRITICAL`, or `MAXIMUM`. If you have to ask, it's probably `HIGH`.

### Adding words via CLI

You can also add words directly from the command line:

```bash
meeting-entropy corpus add --lang fr "paradigme,ecosysteme,roadmap"
```

This appends them to the `custom` category of the specified language corpus.

### Adding a new language

Create a new YAML file in `corpus/` following the format above. Name it `{language_code}.yaml` (e.g., `ja.yaml`, `pt.yaml`). The detector will pick it up automatically when a user passes `--lang {code}`.

## Submitting a Pull Request

1. **Fork** the repository and create a feature branch from `main`:
   ```bash
   git checkout -b add-portuguese-corpus
   ```

2. **Make your changes.** Keep commits focused. One corpus addition per PR is fine; bundling related words together is also fine. Just don't mix corpus changes with code refactors.

3. **Run the tests** (see below). All tests must pass.

4. **Run the linter** (see below). Zero warnings, zero exceptions, zero excuses.

5. **Push and open a PR** against `main`:
   ```bash
   git push origin add-portuguese-corpus
   gh pr create --title "Add Portuguese corpus" --body "Obrigado, corporate nonsense."
   ```

6. **Wait for review.** Kevin Sigmoid reviews all PRs. He is thorough, occasionally pedantic, and always right (in his own mind). Expect constructive feedback. Do not expect it quickly -- Kevin has meetings to endure.

### What makes a good PR

- A clear title and description.
- Tests for any new code (corpus-only PRs are exempt).
- No unrelated changes.
- No files that smell like secrets (`.env`, credentials, API keys). The CI will catch these, and Kevin will judge you.

## Code Style

This project uses **[ruff](https://docs.astral.sh/ruff/)** for linting and formatting. The configuration lives in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"
```

Before submitting:

```bash
# Check for issues
ruff check .

# Auto-fix what can be auto-fixed
ruff check --fix .

# Format code
ruff format .
```

There is no debate about code style. Ruff has decided. We have all moved on.

## Testing

Tests use **[pytest](https://docs.pytest.org/)** and live in the `tests/` directory.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=meeting_entropy

# Run a specific test file
pytest tests/test_detector.py
```

### Writing tests

- Test files go in `tests/` and must start with `test_`.
- Use descriptive test names. `test_detect_synergy_contamination_finds_exact_match` is good. `test_thing` is not.
- Mock external dependencies (PyAudio, Whisper models) in unit tests. Nobody wants CI to require a microphone.
- If your test needs a corpus fixture, put it in `tests/fixtures/`.

## License

meeting-entropy is licensed under **AGPL-3.0-only**. By submitting a pull request, you agree that your contribution will be licensed under the same terms.

In plain language: your code stays open. Forks stay open. Corporate forks that strip out the sarcasm and sell it as "AI Meeting Analytics Pro" stay open too. That is the point.

If you are not comfortable with AGPL-3.0, that is completely fine -- but please do not submit a PR. Kevin respects boundaries.

---

*"The only thing worse than a meeting is a meeting about meetings. The only thing worse than that is a codebase without tests."*
-- Kevin Sigmoid, probably
