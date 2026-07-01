"""Device-environment plumbing for tomd.

tomd does not bundle MarkItDown. It is a GUI over the `markitdown` CLI
(https://github.com/microsoft/markitdown) installed on the user's machine —
either one already on PATH, or one tomd installs into a private virtualenv
under the user's application-support directory.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

_WINDOWS = sys.platform == "win32"
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if _WINDOWS else 0

_PYTHON3_NAME = re.compile(r"^python3\.\d+(\.exe)?$")


def extra_path_dirs() -> list[str]:
    """Common tool locations a GUI app's minimal PATH won't include.

    GUI apps on macOS launch with a minimal PATH (no /opt/homebrew/bin etc.),
    so these are appended before resolving executables. Python.org's macOS
    installer doesn't always leave a `python3` symlink on that minimal PATH
    either, so its Framework install locations are globbed in too — versions
    are unknown ahead of time, so this can't be a fixed list.
    """
    dirs = [
        "/opt/homebrew/bin",
        "/usr/local/bin",
        str(Path.home() / ".local" / "bin"),
        str(Path.home() / ".cargo" / "bin"),
    ]
    if sys.platform == "darwin":
        dirs += [str(p) for p in Path("/Library/Frameworks/Python.framework/Versions").glob("*/bin")]
    if _WINDOWS:
        programs = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python"
        dirs += [str(p) for p in programs.glob("Python3*")]
    return dirs


def env_with_path() -> dict:
    env = os.environ.copy()
    parts = [p for p in env.get("PATH", "").split(os.pathsep) if p]
    for directory in extra_path_dirs():
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


def _python_candidates() -> list[str]:
    """All plausible Python 3 interpreters on the device, newest first.

    Not tied to a fixed version list — a hardcoded name like "python3.13"
    misses anything newer (e.g. 3.14+) that isn't also symlinked as `python3`.
    Instead, every PATH directory is scanned for `python3.<N>`-style binaries.
    """
    seen: dict[str, None] = {}  # ordered set, keyed by resolved real path

    def add(path: str):
        try:
            real = str(Path(path).resolve())
        except OSError:
            real = path
        seen.setdefault(real, None)

    for name in ("python3", "python"):
        exe = which(name)
        if exe:
            add(exe)

    for directory in env_with_path()["PATH"].split(os.pathsep):
        try:
            entries = os.listdir(directory)
        except OSError:
            continue
        for entry in entries:
            if _PYTHON3_NAME.match(entry):
                add(str(Path(directory) / entry))

    def sort_key(path: str):
        match = re.search(r"python3\.(\d+)", path)
        return int(match.group(1)) if match else -1

    return sorted(seen, key=sort_key, reverse=True)


def find_python():
    """Locate a Python >= 3.10 on the device. Returns (path, version) or (None, None)."""
    for exe in _python_candidates():
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


_UV_INSTALL_URL = (
    "https://astral.sh/uv/install.ps1" if _WINDOWS else "https://astral.sh/uv/install.sh"
)


def install_uv(on_line) -> tuple[bool, str]:
    """Bootstrap uv via its official installer — a small, no-admin-password
    binary that can then fetch its own isolated Python. This is what unblocks
    setup on a bare machine that has no Python at all.

    The installer URL is a fixed literal (never built from user input or
    interpolation) downloaded ourselves and executed from a local file, rather
    than piping a remote script straight into a shell.
    """
    import tempfile
    import urllib.request

    on_line(f"Downloading the uv installer from {_UV_INSTALL_URL}…")
    try:
        with urllib.request.urlopen(_UV_INSTALL_URL, timeout=30) as resp:
            script = resp.read()
    except Exception as exc:
        return False, f"Could not download the uv installer: {exc}"
    if not script:
        return False, "The uv installer downloaded empty."

    suffix = ".ps1" if _WINDOWS else ".sh"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(script)
        tmp_path = tmp.name
    try:
        if _WINDOWS:
            cmd = ["powershell", "-ExecutionPolicy", "ByPass", "-File", tmp_path]
        else:
            cmd = ["sh", tmp_path]
        if run_streamed(cmd, on_line) != 0:
            return False, "Running the uv installer failed."
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if not which("uv"):
        return False, "uv installed but could not be located afterward."
    return True, ""


def install_homebrew_python(on_line) -> tuple[bool, str]:
    """Install a system Python via Homebrew — the explicit alternative to the
    uv bootstrap, for users who want a 'real' system-wide Python.

    Only runs `brew install` when Homebrew itself is already present: Homebrew's
    own first-time installer expects an interactive sudo prompt, which a GUI
    app can't safely relay, so that case is left to the caller to surface as a
    copy-pasteable Terminal command instead of attempting it here.
    """
    brew = which("brew")
    if not brew:
        return False, "HOMEBREW_MISSING"
    on_line("Installing Python via Homebrew…")
    if run_streamed([brew, "install", "python@3.12"], on_line) != 0:
        return False, "Installing Python via Homebrew failed."
    return True, ""


def install_markitdown(on_line) -> tuple[bool, str]:
    """Create tomd's private venv and install markitdown[all] into it.

    Prefers uv (which can download a Python by itself); falls back to a
    device Python >= 3.10 with venv + pip. If neither is present, bootstraps
    uv first so setup can complete on a bare machine.
    """
    venv_dir = managed_venv_dir()
    venv_dir.parent.mkdir(parents=True, exist_ok=True)
    uv = which("uv")
    python, _version = find_python()
    if not uv and not python:
        on_line("No Python or uv found on this device — installing uv…")
        ok, err = install_uv(on_line)
        if not ok:
            return False, f"Could not install uv automatically: {err}"
        uv = which("uv")
        if not uv:
            return False, "uv installed but could not be located afterward."
    try:
        if uv:
            if run_streamed([uv, "venv", "--python", "3.12", venv_dir], on_line) != 0:
                return False, "Creating the environment with uv failed."
            python = venv_executable("python")
            if run_streamed([uv, "pip", "install", "--python", python, "markitdown[all]"], on_line) != 0:
                return False, "Installing markitdown with uv failed."
        else:
            python, version = find_python()  # re-check: install_uv above may have run
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
