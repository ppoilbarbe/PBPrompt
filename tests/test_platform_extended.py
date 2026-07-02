"""Extended platform tests covering notify, set_autostart, remove_autostart."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# platform/__init__.py — platform selection (win32 / darwin branches)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("platform_name", ["win32", "darwin"])
def test_platform_selection_other_os(platform_name: str) -> None:
    """Reload pbprompt.platform with a non-Linux sys.platform to cover lines 23/25."""
    import importlib  # noqa: PLC0415

    import pbprompt.platform as plat  # noqa: PLC0415

    with patch.object(sys, "platform", platform_name):
        importlib.reload(plat)
        assert callable(plat.get_config_dir)

    # Restore: reload with the real (Linux) platform
    importlib.reload(plat)


# ---------------------------------------------------------------------------
# Linux platform
# ---------------------------------------------------------------------------


class TestLinuxNotify:
    def test_notify_no_notify_send(self, caplog: pytest.LogCaptureFixture) -> None:
        import logging  # noqa: PLC0415

        import pbprompt.platform.linux as linux

        with (
            caplog.at_level(logging.DEBUG, logger="pbprompt.platform.linux"),
            patch.object(linux.shutil, "which", return_value=None),
        ):
            linux.notify("Title", "Body")
        assert "notify-send not found" in caplog.text

    def test_notify_with_notify_send(self) -> None:
        import pbprompt.platform.linux as linux

        with (
            patch.object(linux.shutil, "which", return_value="/usr/bin/notify-send"),
            patch.object(linux.subprocess, "run") as mock_run,
        ):
            linux.notify("Title", "Body")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "notify-send"
        assert "Title" in args
        assert "Body" in args

    def test_notify_subprocess_exception(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging  # noqa: PLC0415

        import pbprompt.platform.linux as linux

        with (
            caplog.at_level(logging.DEBUG, logger="pbprompt.platform.linux"),
            patch.object(linux.shutil, "which", return_value="/usr/bin/notify-send"),
            patch.object(linux.subprocess, "run", side_effect=OSError("broken")),
        ):
            linux.notify("Title", "Body")  # must not raise
        assert "notify-send failed" in caplog.text


class TestLinuxSetAutostart:
    def test_set_autostart_enabled(self, tmp_path: Path) -> None:
        import pbprompt.platform.linux as linux

        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with (
            patch.object(linux.Path, "home", return_value=fake_home),
            patch.object(linux.shutil, "which", return_value="/usr/bin/pbprompt"),
        ):
            linux.set_autostart(enabled=True)

        desktop = fake_home / ".config" / "autostart" / "pbprompt.desktop"
        assert desktop.exists()
        content = desktop.read_text()
        assert "Exec=/usr/bin/pbprompt" in content
        assert "[Desktop Entry]" in content

    def test_set_autostart_disabled_calls_remove(self, tmp_path: Path) -> None:
        import pbprompt.platform.linux as linux

        with patch("pbprompt.platform.linux.remove_autostart") as mock_remove:
            linux.set_autostart(enabled=False)
        mock_remove.assert_called_once()

    def test_set_autostart_which_falls_back(self, tmp_path: Path) -> None:
        import pbprompt.platform.linux as linux

        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with (
            patch.object(linux.Path, "home", return_value=fake_home),
            patch.object(linux.shutil, "which", return_value=None),
        ):
            linux.set_autostart(enabled=True)

        desktop = fake_home / ".config" / "autostart" / "pbprompt.desktop"
        assert "Exec=pbprompt" in desktop.read_text()


class TestLinuxRemoveAutostart:
    def test_remove_autostart_no_file(self, tmp_path: Path) -> None:
        import pbprompt.platform.linux as linux

        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with patch.object(linux.Path, "home", return_value=fake_home):
            linux.remove_autostart()  # must not raise — file doesn't exist

    def test_remove_autostart_existing_file(self, tmp_path: Path) -> None:
        import pbprompt.platform.linux as linux

        fake_home = tmp_path / "home"
        desktop_dir = fake_home / ".config" / "autostart"
        desktop_dir.mkdir(parents=True)
        desktop = desktop_dir / "pbprompt.desktop"
        desktop.write_text("[Desktop Entry]\n")

        with patch.object(linux.Path, "home", return_value=fake_home):
            linux.remove_autostart()

        assert not desktop.exists()


# ---------------------------------------------------------------------------
# Windows platform (tested on Linux — only non-winreg branches are covered)
# ---------------------------------------------------------------------------


class TestWindowsPlatform:
    def test_get_config_dir_returns_path(self) -> None:
        from pbprompt.platform.windows import get_config_dir

        result = get_config_dir()
        assert isinstance(result, Path)

    def test_notify_win10toast_not_installed(self) -> None:
        from pbprompt.platform import windows

        # On Linux win10toast is not available → ImportError branch is taken.
        # We enforce it by ensuring the import fails.
        with patch.dict("sys.modules", {"win10toast": None}):
            windows.notify("Title", "Body")  # must not raise

    def test_notify_win10toast_installed(self) -> None:
        from pbprompt.platform import windows

        mock_module = MagicMock()
        mock_notifier = MagicMock()
        mock_module.ToastNotifier.return_value = mock_notifier

        with patch.dict("sys.modules", {"win10toast": mock_module}):
            windows.notify("Title", "Body")

        mock_notifier.show_toast.assert_called_once()

    def test_notify_toastnotifier_exception(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging  # noqa: PLC0415

        from pbprompt.platform import windows

        mock_module = MagicMock()
        mock_module.ToastNotifier.side_effect = RuntimeError("crash")

        with (
            caplog.at_level(logging.DEBUG, logger="pbprompt.platform.windows"),
            patch.dict("sys.modules", {"win10toast": mock_module}),
        ):
            windows.notify("Title", "Body")  # must not raise
        assert "Windows notification failed" in caplog.text

    def test_set_autostart_non_windows_returns_early(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        from pbprompt.platform import windows

        with patch.object(sys, "platform", "linux"):
            windows.set_autostart(enabled=True)
        assert "non-Windows" in caplog.text

    def test_remove_autostart_non_windows_returns_early(self) -> None:
        from pbprompt.platform import windows

        with patch.object(sys, "platform", "linux"):
            windows.remove_autostart()  # silent no-op on non-Windows

    def test_set_autostart_windows_enabled(self) -> None:
        from pbprompt.platform import windows

        mock_winreg = MagicMock()
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value = mock_key

        with (
            patch.dict("sys.modules", {"winreg": mock_winreg}),
            patch.object(sys, "platform", "win32"),
            patch("shutil.which", return_value="C:\\pbprompt.exe"),
        ):
            windows.set_autostart(enabled=True)

        mock_winreg.SetValueEx.assert_called_once()
        mock_winreg.CloseKey.assert_called_once_with(mock_key)

    def test_set_autostart_windows_disabled(self) -> None:
        from pbprompt.platform import windows

        mock_winreg = MagicMock()
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value = mock_key

        with (
            patch.dict("sys.modules", {"winreg": mock_winreg}),
            patch.object(sys, "platform", "win32"),
            patch("pbprompt.platform.windows.remove_autostart") as mock_remove,
        ):
            windows.set_autostart(enabled=False)

        mock_remove.assert_called_once()

    def test_set_autostart_windows_exception(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        from pbprompt.platform import windows

        mock_winreg = MagicMock()
        mock_winreg.OpenKey.side_effect = OSError("access denied")

        with (
            patch.dict("sys.modules", {"winreg": mock_winreg}),
            patch.object(sys, "platform", "win32"),
        ):
            windows.set_autostart(enabled=True)  # must not raise
        assert "Failed to set autostart" in caplog.text

    def test_remove_autostart_windows_success(self) -> None:
        from pbprompt.platform import windows

        mock_winreg = MagicMock()
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value = mock_key

        with (
            patch.dict("sys.modules", {"winreg": mock_winreg}),
            patch.object(sys, "platform", "win32"),
        ):
            windows.remove_autostart()

        mock_winreg.DeleteValue.assert_called_once_with(mock_key, "PBPrompt")

    def test_remove_autostart_windows_key_not_found(self) -> None:
        from pbprompt.platform import windows

        mock_winreg = MagicMock()
        mock_winreg.OpenKey.side_effect = FileNotFoundError

        with (
            patch.dict("sys.modules", {"winreg": mock_winreg}),
            patch.object(sys, "platform", "win32"),
        ):
            windows.remove_autostart()  # FileNotFoundError → silently ignored

    def test_remove_autostart_windows_unexpected_exception(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        from pbprompt.platform import windows

        mock_winreg = MagicMock()
        mock_winreg.OpenKey.side_effect = PermissionError("access denied")

        with (
            patch.dict("sys.modules", {"winreg": mock_winreg}),
            patch.object(sys, "platform", "win32"),
        ):
            windows.remove_autostart()  # PermissionError → except Exception
        assert "Failed to remove autostart" in caplog.text


# ---------------------------------------------------------------------------
# macOS platform (tested on Linux — subprocess calls are mocked)
# ---------------------------------------------------------------------------


class TestMacosPlatform:
    def test_get_config_dir_returns_path(self) -> None:
        from pbprompt.platform.macos import get_config_dir

        result = get_config_dir()
        assert isinstance(result, Path)

    def test_notify_osascript_not_found(self, caplog: pytest.LogCaptureFixture) -> None:
        import logging  # noqa: PLC0415

        from pbprompt.platform import macos

        with (
            caplog.at_level(logging.DEBUG, logger="pbprompt.platform.macos"),
            patch.object(macos.shutil, "which", return_value=None),
        ):
            macos.notify("Title", "Body")
        assert "osascript not available" in caplog.text

    def test_notify_osascript_found(self) -> None:
        from pbprompt.platform import macos

        with (
            patch.object(macos.shutil, "which", return_value="/usr/bin/osascript"),
            patch.object(macos.subprocess, "run") as mock_run,
        ):
            macos.notify("Title", "Body")
        mock_run.assert_called_once()

    def test_notify_subprocess_exception(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging  # noqa: PLC0415

        from pbprompt.platform import macos

        with (
            caplog.at_level(logging.DEBUG, logger="pbprompt.platform.macos"),
            patch.object(macos.shutil, "which", return_value="/usr/bin/osascript"),
            patch.object(macos.subprocess, "run", side_effect=OSError("broken")),
        ):
            macos.notify("Title", "Body")  # must not raise
        assert "osascript notification failed" in caplog.text

    def test_set_autostart_enabled(self, tmp_path: Path) -> None:
        from pbprompt.platform import macos

        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with (
            patch.object(macos.Path, "home", return_value=fake_home),
            patch.object(macos.shutil, "which", return_value="/usr/bin/pbprompt"),
            patch.object(macos.subprocess, "run", return_value=MagicMock()),
        ):
            macos.set_autostart(enabled=True)

        plist = fake_home / "Library" / "LaunchAgents" / "com.pbsoft.pbprompt.plist"
        assert plist.exists()
        assert "/usr/bin/pbprompt" in plist.read_text()

    def test_set_autostart_disabled_calls_remove(self) -> None:
        from pbprompt.platform import macos

        with patch("pbprompt.platform.macos.remove_autostart") as mock_remove:
            macos.set_autostart(enabled=False)
        mock_remove.assert_called_once()

    def test_remove_autostart_no_file(self, tmp_path: Path) -> None:
        from pbprompt.platform import macos

        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with patch.object(macos.Path, "home", return_value=fake_home):
            macos.remove_autostart()  # no-op, file doesn't exist

    def test_remove_autostart_existing_file(self, tmp_path: Path) -> None:
        from pbprompt.platform import macos

        fake_home = tmp_path / "home"
        agents_dir = fake_home / "Library" / "LaunchAgents"
        agents_dir.mkdir(parents=True)
        plist = agents_dir / "com.pbsoft.pbprompt.plist"
        plist.write_text("<plist></plist>")

        with (
            patch.object(macos.Path, "home", return_value=fake_home),
            patch.object(macos.subprocess, "run", return_value=MagicMock()),
        ):
            macos.remove_autostart()

        assert not plist.exists()
