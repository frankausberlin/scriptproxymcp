"""Tests for the askpass helper script."""

from __future__ import annotations

import pytest

from scriptproxymcp import askpass_gui


def test_main_returns_test_password(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify the helper exits successfully in headless test mode."""
    monkeypatch.setenv("TEST_SUDO_PASSWORD", "secret-password")

    with pytest.raises(SystemExit) as exc_info:
        askpass_gui.main()

    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert captured.out.strip() == "secret-password"
