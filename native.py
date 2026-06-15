"""OS-level integration Qt doesn't expose: hiding the macOS Dock icon
(menu-bar-only mode), showing a window on every Space, and registering a
login item so tomd can start at boot.

Everything here is defensive: on a platform that doesn't support a feature, or
if the optional macOS bindings (pyobjc) aren't installed, the call is a no-op
that returns False instead of raising.
"""

import sys
from pathlib import Path

IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform == "win32"

LOGIN_LABEL = "me.thekiwidev.tomd"


def _appkit():
    try:
        import AppKit
        return AppKit
    except Exception:
        return None


def _launch_command() -> list[str]:
    """The argv that should relaunch tomd — the frozen app bundle/exe when
    packaged, otherwise the dev `python app.py`."""
    if getattr(sys, "frozen", False):
        return [sys.executable]
    return [sys.executable, str(Path(__file__).resolve().parent / "app.py")]


# ---- macOS Dock icon (menu-bar-only mode) ----
def set_dock_icon_visible(visible: bool) -> bool:
    """Show/hide the app's macOS Dock icon. Hidden => menu-bar-only
    ('accessory') app. No-op off macOS or without pyobjc."""
    appkit = _appkit()
    if not IS_MAC or appkit is None:
        return False
    app = appkit.NSApplication.sharedApplication()
    policy = (appkit.NSApplicationActivationPolicyRegular if visible
              else appkit.NSApplicationActivationPolicyAccessory)
    app.setActivationPolicy_(policy)
    return True


# ---- macOS: show a window on every Space ----
def show_on_all_spaces(window) -> bool:
    """Make a Qt window join every Space and float over full-screen apps.
    `window` is a QWidget (must already be created/shown). No-op off macOS."""
    appkit = _appkit()
    if not IS_MAC or appkit is None:
        return False
    try:
        import objc
        view = objc.objc_object(c_void_p=int(window.winId()))
        nswindow = view.window()
        if nswindow is None:
            return False
        behavior = (nswindow.collectionBehavior()
                    | appkit.NSWindowCollectionBehaviorCanJoinAllSpaces
                    | appkit.NSWindowCollectionBehaviorFullScreenAuxiliary)
        nswindow.setCollectionBehavior_(behavior)
        return True
    except Exception:
        return False


# ---- start at login ----
def _mac_plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LOGIN_LABEL}.plist"


def _win_run_key():
    import winreg
    return winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_ALL_ACCESS,
    )


def is_login_item_enabled() -> bool:
    if IS_MAC:
        return _mac_plist_path().exists()
    if IS_WIN:
        try:
            import winreg
            with _win_run_key() as key:
                winreg.QueryValueEx(key, "tomd")
            return True
        except OSError:
            return False
    return False


def set_login_item(enabled: bool) -> bool:
    """Register/unregister tomd to start at login. Returns True if applied."""
    if IS_MAC:
        return _set_login_item_mac(enabled)
    if IS_WIN:
        return _set_login_item_win(enabled)
    return False


def _set_login_item_mac(enabled: bool) -> bool:
    path = _mac_plist_path()
    if not enabled:
        path.unlink(missing_ok=True)
        return True
    args = "".join(f"        <string>{a}</string>\n" for a in _launch_command())
    plist = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        '<dict>\n'
        f'    <key>Label</key>\n    <string>{LOGIN_LABEL}</string>\n'
        '    <key>ProgramArguments</key>\n    <array>\n'
        f'{args}'
        '    </array>\n'
        '    <key>RunAtLoad</key>\n    <true/>\n'
        '</dict>\n'
        '</plist>\n'
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(plist, encoding="utf-8")
    return True


def _set_login_item_win(enabled: bool) -> bool:
    import winreg
    cmd = " ".join(f'"{a}"' for a in _launch_command())
    try:
        with _win_run_key() as key:
            if enabled:
                winreg.SetValueEx(key, "tomd", 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, "tomd")
                except OSError:
                    pass
        return True
    except OSError:
        return False
