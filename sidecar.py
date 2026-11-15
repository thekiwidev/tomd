"""tomd sidecar: runs backend.py for the desktop shell.

A long-lived process speaking JSON lines. One request per line on stdin:

    {"id": 1, "method": "convert_file", "params": {...}}

Replies on stdout, any number of log lines then exactly one result:

    {"id": 1, "event": "log", "line": "..."}
    {"id": 1, "event": "result", "ok": true, "data": ...}
    {"id": 1, "event": "result", "ok": false, "error": "..."}

Each request runs on its own thread, so a long install doesn't block a
conversion. When stdin closes (the shell quit or died) the process finishes
the requests already running and exits.
"""

import json
import sys
import threading
from pathlib import Path

import backend
import links

# stdout carries the protocol and nothing else: anything backend or a library
# prints must not corrupt it.
_out = sys.stdout
sys.stdout = sys.stderr
_write_lock = threading.Lock()


def _emit(message: dict):
    with _write_lock:
        _out.write(json.dumps(message, default=str) + "\n")
        _out.flush()


def _outcome(result: tuple, **extra):
    """backend's (ok, detail) pairs: detail is the payload on success and the
    error text on failure."""
    ok, detail = result
    if not ok:
        raise RuntimeError(detail or "Failed")
    return {"detail": detail, **extra}


def _managed_markitdown() -> str:
    return str(backend.venv_executable("markitdown"))


def environment_report(log, deep=True):
    return {**backend.environment_report(deep=deep),
            "venv_dir": str(backend.managed_venv_dir())}


def find_foreign_markitdowns(log):
    return backend.find_foreign_markitdowns()


def invalidate_health_cache(log):
    backend.invalidate_health_cache()


def install_markitdown(log):
    return _outcome(backend.install_markitdown(log), markitdown=_managed_markitdown())


def install_homebrew_python(log):
    return _outcome(backend.install_homebrew_python(log), markitdown=_managed_markitdown())


def repair_markitdown(log, deep_targets=()):
    return _outcome(backend.repair_markitdown(log, tuple(deep_targets)),
                    markitdown=_managed_markitdown())


def convert_file(log, markitdown_exe, source, output=None, expect_transcript=False):
    # A local file's Markdown goes beside it; only URLs need an explicit output.
    target = Path(output) if output else Path(source).with_suffix(".md")
    return _outcome(backend.convert_file(
        markitdown_exe, source, target, expect_transcript=expect_transcript))


def collect_paths(log, paths):
    return [str(p) for p in links.collect_paths(paths)]


def youtube_plan(log, url, title="", folder="", taken=()):
    """Validate a link and say what file it would produce. `error` is None for
    a usable link; both `error` and `video_id` are None for empty input."""
    video_id, error = links.parse_youtube_url(url)
    if not video_id:
        return {"video_id": None, "error": error}
    slug = links.slugify(title, video_id)
    plan = {"video_id": video_id, "error": None, "slug": slug,
            "url": links.canonical_youtube_url(video_id)}
    if folder:
        plan["output"] = str(links.unique_output(
            Path(folder), slug, taken={Path(t) for t in taken}))
    return plan


METHODS = {f.__name__: f for f in (
    environment_report, find_foreign_markitdowns, invalidate_health_cache,
    install_markitdown, install_homebrew_python, repair_markitdown,
    convert_file, collect_paths, youtube_plan,
)}


def handle(request: dict, emit=_emit):
    """Run one request and emit its log lines and single result."""
    req_id = request.get("id")
    try:
        method = METHODS[request["method"]]
        data = method(
            lambda line: emit({"id": req_id, "event": "log", "line": line}),
            **(request.get("params") or {}),
        )
        emit({"id": req_id, "event": "result", "ok": True, "data": data})
    except KeyError as exc:
        emit({"id": req_id, "event": "result", "ok": False,
              "error": f"Unknown or malformed request: {exc}"})
    except Exception as exc:  # a failed request must not take the sidecar down
        emit({"id": req_id, "event": "result", "ok": False, "error": str(exc)})


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except ValueError:
            _emit({"id": None, "event": "result", "ok": False, "error": "Invalid JSON"})
            continue
        threading.Thread(target=handle, args=(request,)).start()
    # stdin closed: the shell is gone. Returning lets in-flight requests finish
    # (non-daemon threads) — killing an install halfway leaves a broken venv.


if __name__ == "__main__":
    main()
