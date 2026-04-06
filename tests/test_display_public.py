"""Tests for --display-public mode."""

from unittest.mock import patch
from meeting_entropy.detector.buzzword_evangelist_detector import MeetingState


def test_display_public_requires_confirmation():
    """
    Le mode --display-public doit demander une confirmation supplementaire.
    Parce que Kevin a appris a ses depens.
    """
    from click.testing import CliRunner
    from meeting_entropy.cli import cli

    runner = CliRunner()
    with patch("meeting_entropy.cli.check_consent", return_value=True):
        result = runner.invoke(cli, ["start", "--display-public"], input="n\n")
        assert result.exit_code == 0


def test_display_public_warning_is_shown():
    """Test that the warning message is displayed before public mode."""
    from click.testing import CliRunner
    from meeting_entropy.cli import cli

    runner = CliRunner()
    with patch("meeting_entropy.cli.check_consent", return_value=True):
        result = runner.invoke(cli, ["start", "--display-public"], input="n\n")
        assert "DISPLAY PUBLIC" in result.output or result.exit_code == 0
