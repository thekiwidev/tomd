"""Device-environment plumbing for tomd.

tomd does not bundle MarkItDown. It is a GUI over the `markitdown` CLI
(https://github.com/microsoft/markitdown) installed on the user's machine —
either one already on PATH, or one tomd installs into a private virtualenv
under the user's application-support directory.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# GUI apps on macOS launch with a minimal PATH (no /opt/homebrew/bin etc.),
# so common tool locations are appended before resolving executables.
EXTRA_PATH_DIRS = [
    "/opt/homebrew/bin",
    "/usr/local/bin",
    str(Path.home() / ".local" / "bin"),
    str(Path.home() / ".cargo" / "bin"),
]

_WINDOWS = sys.platform == "win32"
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if _WINDOWS else 0


def env_with_path() -> dict:
    env = os.environ.copy()
    parts = [p for p in env.get("PATH", "").split(os.pathsep) if p]
    for directory in EXTRA_PATH_DIRS:
        if directory not in parts:
            parts.append(directory)
    env["PATH"] = os.pathsep.join(parts)
    return env


def which(command: str):
    return shutil.which(command, path=env_with_path()["PATH"])


def app_data_dir() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif _WINDOWS:
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "tomd"


def managed_venv_dir() -> Path:
    return app_data_dir() / "venv"


def venv_executable(name: str) -> Path:
    sub = "Scripts" if _WINDOWS else "bin"
    suffix = ".exe" if _WINDOWS else ""
    return managed_venv_dir() / sub / f"{name}{suffix}"


def resolve_markitdown():
    """Find the markitdown CLI: user's PATH first, then tomd's managed venv."""
    on_path = which("markitdown")
    if on_path:
        return on_path
    managed = venv_executable("markitdown")
    if managed.exists():
        return str(managed)
    return None


def find_python():
    """Locate a Python >= 3.10 on the device. Returns (path, version) or (None, None)."""
    for name in ("python3.13", "python3.12", "python3.11", "python3.10", "python3", "python"):
        exe = which(name)
        if not exe:
            continue
        try:
            out = subprocess.check_output(
                [exe, "--version"], text=True, stderr=subprocess.STDOUT,
                env=env_with_path(), creationflags=_NO_WINDOW,
            ).strip()
            version = out.split()[1]
            major, minor = (int(x) for x in version.split(".")[:2])
            if (major, minor) >= (3, 10):
                return exe, version
        except Exception:
            continue
    return None, None


def environment_report() -> dict:
    """Snapshot of what the device has, for the setup screen."""
    python_exe, python_version = find_python()
    return {
        "markitdown": resolve_markitdown(),
        "python": python_exe,
        "python_version": python_version,
        "uv": which("uv"),
    }


def run_streamed(cmd, on_line) -> int:
    """Run a command, feeding each output line to on_line. Returns exit code."""
    on_line("$ " + " ".join(str(c) for c in cmd))
    proc = subprocess.Popen(
        [str(c) for c in cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, env=env_with_path(), creationflags=_NO_WINDOW,
    )
    for line in proc.stdout:
        line = line.rstrip()
        if line:
            on_line(line)
    return proc.wait()


def install_markitdown(on_line) -> tuple[bool, str]:
    """Create tomd's private venv and install markitdown[all] into it.

    Prefers uv (which can download a Python by itself); falls back to a
    device Python >= 3.10 with venv + pip.
    """
    venv_dir = managed_venv_dir()
    venv_dir.parent.mkdir(parents=True, exist_ok=True)
    uv = which("uv")
    try:
        if uv:
            if run_streamed([uv, "venv", "--python", "3.12", venv_dir], on_line) != 0:
                return False, "Creating the environment with uv failed."
            python = venv_executable("python")
            if run_streamed([uv, "pip", "install", "--python", python, "markitdown[all]"], on_line) != 0:
                return False, "Installing markitdown with uv failed."
        else:
            python, version = find_python()
            if not python:
                return False, (
                    "No Python 3.10+ found on this device. Install Python from "
                    "https://python.org or run `brew install python`, then retry."
                )
            on_line(f"Using {python} (Python {version})")
            if run_streamed([python, "-m", "venv", venv_dir], on_line) != 0:
                return False, "Creating the virtual environment failed."
            venv_python = venv_executable("python")
            if run_streamed([venv_python, "-m", "pip", "install", "--upgrade", "pip"], on_line) != 0:
                return False, "Upgrading pip failed."
            if run_streamed([venv_python, "-m", "pip", "install", "markitdown[all]"], on_line) != 0:
                return False, "Installing markitdown failed."
        if not venv_executable("markitdown").exists():
            return False, "Install finished but the markitdown command was not found."
        return True, ""
    except Exception as exc:  # noqa: BLE001 — report any setup failure to the UI
        return False, str(exc)


def convert_file(markitdown_exe: str, source: Path) -> tuple[bool, str]:
    """Convert one file with the device's markitdown CLI.

    Returns (True, output_path) or (False, error_message).
    """
    output = source.with_suffix(".md")
    try:
        proc = subprocess.run(
            [markitdown_exe, str(source), "-o", str(output)],
            capture_output=True, text=True, env=env_with_path(), creationflags=_NO_WINDOW,
        )
    except OSError as exc:
        return False, str(exc)
    if proc.returncode == 0 and output.exists():
        return True, str(output)
    message = (proc.stderr or proc.stdout or f"markitdown exited with code {proc.returncode}").strip()
    return False, message[-500:]
