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

# The oldest markitdown release tomd will accept. Not a pin — there is
# deliberately no upper bound, so installs always land on the newest release.
# The floor exists because releases below it predate the `[all]` extra
# entirely: without it, pip is free to backtrack all the way to 0.0.2 when a
# newer release's dependency chain can't be resolved, and "succeed" with a CLI
# that silently can't read PDFs, Word, PowerPoint or Excel.
MIN_MARKITDOWN = (0, 1, 0)

# Which import a given markitdown optional feature needs. `markitdown[all]`
# pulls all of these in; a plain `pip install markitdown` pulls in none of
# them, and the CLI only fails at conversion time, one format at a time.
FEATURE_IMPORTS = {
    "core": ["magika"],
    "pdf": ["pdfminer.high_level", "pdfplumber"],
    "docx": ["mammoth", "lxml"],
    "pptx": ["pptx"],
    "xlsx": ["openpyxl"],
    "xls": ["xlrd"],
    "outlook": ["olefile"],
    "audio": ["pydub", "speech_recognition"],
    "youtube": ["youtube_transcript_api"],
}

# Runs inside the *target* interpreter, not this one: imports each feature's
# modules and prints the names of the features that failed.
_PROBE_SOURCE = """
import importlib, json, sys
missing = []
for feature, modules in json.loads(sys.argv[1]).items():
    for module in modules:
        try:
            importlib.import_module(module)
        except Exception:
            missing.append(feature)
            break
print(json.dumps(missing))
"""


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


def interpreter_for(exe) -> Path | None:
    """The Python that runs a console script.

    Console scripts are installed next to the interpreter that owns them (both
    in a venv and in a framework/Homebrew prefix), so the sibling `python3` is
    the one whose site-packages the script actually imports from. Reading the
    shebang would be more direct, but uv writes a `#!/bin/sh` exec-wrapper
    rather than a real interpreter path.
    """
    parent = Path(exe).parent
    for name in ("python3", "python"):
        candidate = parent / (f"{name}.exe" if _WINDOWS else name)
        if candidate.exists():
            return candidate
    return None


def markitdown_version(exe) -> tuple | None:
    """(major, minor, patch) of a markitdown CLI, or None if it won't report.

    Anchored on the "markitdown " prefix rather than the first number in the
    output: markitdown's dependencies emit warnings before it (pydub prints an
    ffmpeg RuntimeWarning quoting a `.../python3.14/...` path), and a loose
    number match happily reads a version out of one of those.
    """
    try:
        out = subprocess.check_output(
            [str(exe), "--version"], text=True, stderr=subprocess.DEVNULL,
            env=env_with_path(), timeout=60, creationflags=_NO_WINDOW,
        ).strip()
    except Exception:
        return None
    match = re.search(r"markitdown\s+v?(\d+)\.(\d+)(?:\.(\d+))?", out, re.IGNORECASE)
    if not match:
        return None
    return tuple(int(part or 0) for part in match.groups())


def _missing_features(python_exe) -> list | None:
    """Feature names whose imports fail in `python_exe`. None if unknowable.

    One subprocess probes every feature at once — nine separate interpreter
    startups would make the settings window visibly stall.
    """
    import json

    try:
        out = subprocess.check_output(
            [str(python_exe), "-c", _PROBE_SOURCE, json.dumps(FEATURE_IMPORTS)],
            text=True, stderr=subprocess.DEVNULL, env=env_with_path(),
            timeout=120, creationflags=_NO_WINDOW,
        )
        return json.loads(out.strip().splitlines()[-1])
    except Exception:
        return None


# Probing an install costs a couple of interpreter startups (importing pandas
# and onnxruntime is not free), so results are memoised for the session and
# dropped explicitly whenever tomd changes an environment.
_health_cache: dict = {}


def invalidate_health_cache():
    _health_cache.clear()


def markitdown_health(exe, use_cache: bool = True) -> dict:
    """Whether a markitdown CLI can actually do the job, not just whether it exists.

    `markitdown --version` succeeding proves very little: a plain
    `pip install markitdown` yields a CLI that converts CSV and text fine and
    raises MissingDependencyException on every PDF, Word, PowerPoint and Excel
    file. That looks intermittent to a user, so it's checked explicitly here.
    """
    key = str(exe)
    if use_cache and key in _health_cache:
        return _health_cache[key]
    version = markitdown_version(exe)
    version_ok = bool(version) and version >= MIN_MARKITDOWN
    python_exe = interpreter_for(exe)
    missing = _missing_features(python_exe) if python_exe else None
    result = {
        "exe": str(exe),
        "version": version,
        "version_str": ".".join(str(p) for p in version) if version else None,
        "version_ok": version_ok,
        "interpreter": str(python_exe) if python_exe else None,
        # None means "couldn't probe" — don't report that as a failure.
        "missing_features": missing,
        "ok": version_ok and not missing,
    }
    _health_cache[key] = result
    return result


def resolve_markitdown(check_health: bool = True):
    """Find the markitdown CLI: user's PATH first, then tomd's managed venv.

    A PATH install only wins if it's actually healthy. Preferring it
    unconditionally lets a half-installed system markitdown shadow the working
    one tomd manages, which is indistinguishable from tomd itself being broken.
    When neither is healthy the PATH one is still returned so the UI has
    something concrete to report and repair.

    `check_health=False` skips the probe entirely and restores the original
    "first one that exists wins" behaviour — used on the startup path, where a
    few seconds of interpreter startups would be a visible freeze.
    """
    on_path = which("markitdown")
    managed = venv_executable("markitdown")
    if not check_health:
        return on_path or (str(managed) if managed.exists() else None)
    if on_path and markitdown_health(on_path)["ok"]:
        return on_path
    if managed.exists() and markitdown_health(managed)["ok"]:
        return str(managed)
    if on_path:
        return on_path
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


def environment_report(deep: bool = True) -> dict:
    """Snapshot of what the device has, for the setup and settings screens.

    `deep=False` omits the health probe (and the `health` key is None). Startup
    uses the shallow form so the window appears immediately; the deep report is
    then gathered on a worker thread.
    """
    python_exe, python_version = find_python()
    markitdown = resolve_markitdown(check_health=deep)
    return {
        "markitdown": markitdown,
        "health": markitdown_health(markitdown) if (deep and markitdown) else None,
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


def _download(url: str, dest: Path, on_line) -> str:
    """Fetch `url` to `dest`. Returns "" on success or an error message.

    Falls back to curl when Python's own TLS can't verify the certificate:
    python.org's macOS framework builds ship an OpenSSL with no CA store until
    "Install Certificates.command" is run, so urlopen fails there with
    CERTIFICATE_VERIFY_FAILED even though the network is fine. curl uses the
    system trust store and is present on every supported platform.
    """
    import urllib.request

    try:
        context = None
        try:
            import certifi
            import ssl
            context = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            pass  # no certifi — use Python's default verification
        with urllib.request.urlopen(url, timeout=30, context=context) as resp:
            data = resp.read()
        if data:
            dest.write_bytes(data)
            return ""
        error = "the download was empty"
    except Exception as exc:
        error = str(exc)

    curl = which("curl")
    if not curl:
        return error
    on_line(f"Direct download failed ({error}) — retrying with curl…")
    if run_streamed([curl, "-fsSL", url, "-o", str(dest)], on_line) != 0:
        return error
    try:
        return "" if dest.stat().st_size else error
    except OSError:
        return error


def install_uv(on_line) -> tuple[bool, str]:
    """Bootstrap uv via its official installer — a small, no-admin-password
    binary that can then fetch its own isolated Python. This is what unblocks
    setup on a machine whose only Python can't install markitdown.

    The installer URL is a fixed literal (never built from user input or
    interpolation) downloaded ourselves and executed from a local file, rather
    than piping a remote script straight into a shell.
    """
    import tempfile

    on_line(f"Downloading the uv installer from {_UV_INSTALL_URL}…")
    suffix = ".ps1" if _WINDOWS else ".sh"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name
    error = _download(_UV_INSTALL_URL, Path(tmp_path), on_line)
    if error:
        Path(tmp_path).unlink(missing_ok=True)
        return False, f"Could not download the uv installer: {error}"

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


# A floor, never a ceiling — pip/uv still resolve the newest release available.
_MARKITDOWN_SPEC = "markitdown[all]>=" + ".".join(str(p) for p in MIN_MARKITDOWN)


def _uv_python_versions(uv: str) -> list[str]:
    """Python minor versions uv can supply, newest first (e.g. ["3.14", "3.13"])."""
    try:
        out = subprocess.check_output(
            [uv, "python", "list"], text=True, stderr=subprocess.DEVNULL,
            env=env_with_path(), timeout=60, creationflags=_NO_WINDOW,
        )
    except Exception:
        return []
    minors = {
        (int(m.group(1)), int(m.group(2)))
        for m in re.finditer(r"cpython-(\d+)\.(\d+)\.", out)
    }
    return [f"{a}.{b}" for a, b in sorted(minors, reverse=True) if (a, b) >= (3, 10)]


def _uv_ladder(uv: str) -> list[tuple]:
    return [("uv", uv, version) for version in _uv_python_versions(uv)]


def _system_ladder() -> list[tuple]:
    return [("system", exe, exe) for exe in _python_candidates()]


def _python_ladder(on_line) -> list[tuple]:
    """Interpreters to try building the venv with, best candidate first.

    Newest-first, but deliberately a *ladder* rather than a single pick. The
    newest Python on a machine is routinely ahead of what markitdown's
    dependency chain supports, and pip's response to that is to backtrack to an
    ancient markitdown rather than to fail — which is how a venv ends up
    holding 0.0.2. Each rung is verified after install, so a rung that can't
    produce a working CLI is discarded and the next one tried.

    Nothing here is version-locked: the newest Python is used the moment its
    wheels exist. uv rungs come first when uv is available, because uv can
    download an interpreter this device doesn't have.
    """
    uv = which("uv")
    python, _version = find_python()
    if not uv and not python:
        on_line("No Python or uv found on this device — installing uv…")
        ok, err = install_uv(on_line)
        if not ok:
            on_line(f"Could not install uv automatically: {err}")
        uv = which("uv")

    ladder = _uv_ladder(uv) if uv else []
    return ladder + _system_ladder()


def _build_venv(kind: str, tool: str, spec: str, venv_dir: Path, on_line) -> str:
    """Create the venv and install markitdown into it. Returns "" or an error."""
    shutil.rmtree(venv_dir, ignore_errors=True)
    if kind == "uv":
        if run_streamed([tool, "venv", "--python", spec, venv_dir], on_line) != 0:
            return f"Creating the environment with uv (Python {spec}) failed."
        venv_python = venv_executable("python")
        if run_streamed(
            [tool, "pip", "install", "--python", venv_python, _MARKITDOWN_SPEC], on_line
        ) != 0:
            return "Installing markitdown with uv failed."
        return ""
    if run_streamed([spec, "-m", "venv", venv_dir], on_line) != 0:
        return "Creating the virtual environment failed."
    venv_python = venv_executable("python")
    if run_streamed([venv_python, "-m", "pip", "install", "--upgrade", "pip"], on_line) != 0:
        on_line("Could not upgrade pip — continuing with the bundled version.")
    if run_streamed([venv_python, "-m", "pip", "install", _MARKITDOWN_SPEC], on_line) != 0:
        return "Installing markitdown failed."
    return ""


def _try_rung(kind, tool, spec, venv_dir, on_line) -> tuple[bool, str]:
    """Build the venv on one interpreter and verify the result. (ok, error)."""
    label = f"uv Python {spec}" if kind == "uv" else str(spec)
    on_line(f"— Trying {label}…")
    try:
        error = _build_venv(kind, tool, spec, venv_dir, on_line)
    except Exception as exc:  # noqa: BLE001 — any failure just fails this rung
        error = str(exc)
    if error:
        on_line(f"{label}: {error}")
        return False, error

    markitdown = venv_executable("markitdown")
    if not markitdown.exists():
        error = "Install finished but the markitdown command was not found."
        on_line(f"{label}: {error}")
        return False, error

    health = markitdown_health(markitdown)
    if not health["version_ok"]:
        found = health["version_str"] or "unknown"
        floor = ".".join(str(p) for p in MIN_MARKITDOWN)
        error = (
            f"Resolved markitdown {found}, older than {floor} — {label} is missing "
            f"wheels for markitdown's dependencies, so pip fell back to an "
            f"obsolete release."
        )
        on_line(f"{label}: {error}")
        return False, error
    if health["missing_features"]:
        missing = ", ".join(health["missing_features"])
        error = f"markitdown installed but these formats are unavailable: {missing}."
        on_line(f"{label}: {error}")
        return False, error

    on_line(f"✓ markitdown {health['version_str']} installed with all formats using {label}.")
    return True, ""


def install_markitdown(on_line) -> tuple[bool, str]:
    """Create tomd's private venv and install markitdown[all] into it.

    Prefers uv (which can download a Python by itself); falls back to a device
    Python >= 3.10 with venv + pip. Every candidate is verified with
    markitdown_health() before being accepted — an install that merely produced
    a `markitdown` file on disk is not a successful install.

    If every interpreter already on the device fails, uv is installed as a last
    resort and its downloadable Pythons are tried too. That escalation is not
    optional politeness: markitdown[all] can be genuinely uninstallable on the
    only Python a machine has (as of writing, its youtube-transcript-api pin
    excludes Python 3.14), and fetching a different interpreter is then the only
    way to finish. uv is skipped entirely when a device Python already works.
    """
    venv_dir = managed_venv_dir()
    venv_dir.parent.mkdir(parents=True, exist_ok=True)
    invalidate_health_cache()

    ladder = _python_ladder(on_line)
    if not ladder:
        return False, (
            "No Python 3.10+ found on this device. Install Python from "
            "https://python.org or run `brew install python`, then retry."
        )

    tried, last_error = [], ""
    for kind, tool, spec in ladder:
        tried.append(f"uv Python {spec}" if kind == "uv" else str(spec))
        ok, last_error = _try_rung(kind, tool, spec, venv_dir, on_line)
        if ok:
            return True, ""

    # Every interpreter on the device failed. If uv wasn't among them it can
    # supply one they don't have, so bootstrap it and try again.
    if not which("uv"):
        on_line("")
        on_line(
            "No Python on this device can install markitdown with all formats. "
            "Installing uv so a compatible Python can be downloaded…"
        )
        ok, err = install_uv(on_line)
        uv = which("uv")
        if not ok or not uv:
            return False, (
                f"Tried {', '.join(tried)}, and could not install uv to fetch "
                f"another Python: {err or 'uv could not be located afterward'}"
            )
        for kind, tool, spec in _uv_ladder(uv):
            tried.append(f"uv Python {spec}")
            ok, last_error = _try_rung(kind, tool, spec, venv_dir, on_line)
            if ok:
                return True, ""

    shutil.rmtree(venv_dir, ignore_errors=True)
    return False, f"Tried {', '.join(tried)}. Last error: {last_error}"


def find_foreign_markitdowns() -> list[dict]:
    """markitdown installs on this device that tomd did not create.

    These matter because one of them may be first on PATH and shadow tomd's
    managed install. Reported so the UI can offer to remove them; never removed
    without being asked, since tomd didn't put them there.
    """
    managed = str(managed_venv_dir())
    found = []
    for python in _python_candidates():
        if python.startswith(managed):
            continue
        try:
            out = subprocess.check_output(
                [python, "-m", "pip", "show", "markitdown"], text=True,
                stderr=subprocess.DEVNULL, env=env_with_path(), timeout=60,
                creationflags=_NO_WINDOW,
            )
        except Exception:
            continue
        fields = {}
        for line in out.splitlines():
            key, _, value = line.partition(":")
            fields[key.strip().lower()] = value.strip()
        location = fields.get("location", "")
        if location.startswith(managed):
            continue
        missing = _missing_features(python)
        found.append({
            "interpreter": python,
            "version": fields.get("version", "unknown"),
            "location": location,
            "healthy": missing == [],
            "missing_features": missing,
        })
    return found


def purge_markitdown(on_line, deep_targets=()) -> tuple[bool, str]:
    """Remove tomd's managed environment and markitdown's build caches.

    Only the managed venv is removed unconditionally — tomd created that
    directory and owns it outright. Anything in `deep_targets` is a foreign
    interpreter the user explicitly asked to clean, and is uninstalled from
    rather than deleted. Cache clears are best-effort: a cache that won't clear
    is not a reason to block the reinstall that follows.
    """
    invalidate_health_cache()
    venv_dir = managed_venv_dir()
    if venv_dir.exists():
        on_line(f"Removing {venv_dir}…")
        try:
            shutil.rmtree(venv_dir)
        except OSError as exc:
            return False, f"Could not remove {venv_dir}: {exc}"
    else:
        on_line(f"No managed environment at {venv_dir} — nothing to remove.")

    pycache = app_data_dir() / "__pycache__"
    if pycache.exists():
        shutil.rmtree(pycache, ignore_errors=True)

    packages = ["markitdown", "magika", "onnxruntime"]
    uv = which("uv")
    if uv:
        on_line("Clearing uv's build cache for markitdown…")
        run_streamed([uv, "cache", "clean", *packages], on_line)

    python, _version = find_python()
    if python:
        on_line("Clearing pip's wheel cache for markitdown…")
        run_streamed([python, "-m", "pip", "cache", "remove", "markitdown*"], on_line)

    for target in deep_targets:
        on_line(f"Uninstalling markitdown from {target}…")
        if run_streamed([target, "-m", "pip", "uninstall", "-y", "markitdown"], on_line) != 0:
            # A system Python may be root-owned; report it and keep going
            # rather than failing the whole repair over it.
            on_line(
                f"Could not uninstall from {target} — it may need administrator "
                f"rights. Run this in Terminal if you want it gone:\n"
                f"  {target} -m pip uninstall -y markitdown"
            )
    return True, ""


def repair_markitdown(on_line, deep_targets=()) -> tuple[bool, str]:
    """Purge tomd's markitdown environment and install it again from scratch."""
    on_line("=== Removing the existing MarkItDown environment ===")
    ok, error = purge_markitdown(on_line, deep_targets)
    if not ok:
        return False, error
    on_line("")
    on_line("=== Installing MarkItDown ===")
    return install_markitdown(on_line)


def convert_file(
    markitdown_exe: str, source, output: Path, expect_transcript: bool = False
) -> tuple[bool, str]:
    """Convert one source with the device's markitdown CLI.

    `source` is a local path or a URL — the CLI takes either in the same
    positional slot, and MarkItDown.convert() routes http/https strings to its
    URI converters (which is what makes YouTube transcripts work). `output` is
    explicit rather than derived from `source`, because a URL has no directory
    to sit next to.

    Returns (True, output_path) or (False, error_message).
    """
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [markitdown_exe, str(source), "-o", str(output)],
            capture_output=True, text=True, env=env_with_path(), creationflags=_NO_WINDOW,
        )
    except OSError as exc:
        return False, str(exc)
    if proc.returncode == 0 and output.exists():
        if expect_transcript:
            problem = _transcript_problem(output, proc.stderr or proc.stdout or "")
            if problem:
                # The file on disk is page furniture, not a transcript. Leaving
                # it would be worse than failing: it looks like a finished job.
                output.unlink(missing_ok=True)
                return False, problem
        return True, str(output)
    message = (proc.stderr or proc.stdout or f"markitdown exited with code {proc.returncode}").strip()
    return False, _readable_error(message)


def _transcript_problem(output: Path, stderr: str) -> str:
    """Why a YouTube conversion produced no transcript, or "" if it did.

    MarkItDown exits 0 even when the transcript fetch fails: its YouTube
    converter gives up, the generic HTML converter handles the page instead,
    and the result is a file of YouTube's footer links reported as a success.
    Nothing in the exit code or the output path reveals that, so the file's
    content is what gets checked.
    """
    try:
        text = output.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"Could not read the converted file: {exc}"
    if "### Transcript" in text:
        return ""
    hinted = _readable_error(stderr)
    if hinted and hinted != stderr[-500:]:
        return hinted           # a known cause (blocked, captions off, …)
    if "# YouTube" not in text:
        return ("YouTube returned the page but not the video — no transcript was "
                "produced. This usually means YouTube is throttling this network.")
    return ("MarkItDown read the video's details but could not fetch its "
            "transcript. The video may have captions turned off.")


_YOUTUBE_BLOCKED = (
    "YouTube is refusing requests from this network — it returns a bot check "
    "instead of the video page. Turn off any VPN, or try another network "
    "(a phone hotspot usually works)."
)

# Failures whose real cause is invisible in the raw exception. The YouTube ones
# matter most: the underlying error is an HTTP 429 whose message is a 200-char
# Google challenge URL, which tells a user nothing about what to do next.
_ERROR_HINTS = (
    ("google.com/sorry", _YOUTUBE_BLOCKED),
    ("IpBlocked", _YOUTUBE_BLOCKED),
    ("RequestBlocked", _YOUTUBE_BLOCKED),
    ("TooManyRequests", _YOUTUBE_BLOCKED),
    ("too many requests", _YOUTUBE_BLOCKED),
    ("YouTubeRequestFailed", _YOUTUBE_BLOCKED),
    ("TranscriptsDisabled", "This video has captions turned off, so there's no transcript to fetch."),
    ("NoTranscriptFound", "This video has no transcript available in a supported language."),
    ("NoTranscriptAvailable", "This video has no transcript available."),
    ("VideoUnavailable", "That video isn't available — check the link."),
    ("AgeRestricted", "That video is age-restricted, so its transcript can't be fetched."),
    ("MissingDependencyException", "MarkItDown is missing the dependency for this file type — "
                                   "open Settings and run Repair MarkItDown."),
)


def _readable_error(message: str) -> str:
    """The useful line out of a markitdown failure.

    markitdown reports failures as Python tracebacks, and the row that shows
    them is one line tall. Tailing the raw text lands mid-frame — a user
    hitting YouTube's rate limit saw "_status()" rather than the 429. Known
    causes are translated into something actionable; otherwise the last
    non-empty line of the traceback (the exception itself) is what's shown.
    """
    lowered = message.lower()
    for needle, hint in _ERROR_HINTS:
        if needle.lower() not in lowered:
            continue
        # "429 Too Many Requests" happens off YouTube too, where blaming
        # YouTube would be actively misleading.
        if hint is _YOUTUBE_BLOCKED and "youtube" not in lowered:
            continue
        return hint

    lines = [line for line in message.splitlines() if line.strip()]
    if not lines or "Traceback (most recent call last)" not in message:
        return message[-500:]
    # Not lines[0]: markitdown's dependencies warn on stderr before the
    # traceback starts (pydub always warns about ffmpeg), so the traceback is
    # looked for anywhere in the output and the final line taken from the end.
    last = lines[-1]
    # "requests.exceptions.HTTPError: 429 …" reads better as "HTTPError: 429 …"
    match = re.match(r"^([\w.]+)(: .*)$", last, re.DOTALL)
    if match:
        last = match.group(1).rsplit(".", 1)[-1] + match.group(2)
    return last[:500]
