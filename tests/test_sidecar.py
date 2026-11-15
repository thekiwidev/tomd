import json
import subprocess
import sys
from pathlib import Path

import sidecar

ROOT = Path(__file__).resolve().parent.parent
VIDEO = "_0A2BnRYVCo"


def run(requests):
    """Feed requests to a real sidecar process; replies keyed by request id."""
    proc = subprocess.run(
        [sys.executable, str(ROOT / "sidecar.py")],
        input="".join(json.dumps(r) + "\n" for r in requests),
        capture_output=True, text=True, timeout=60, cwd=ROOT,
    )
    replies = [json.loads(line) for line in proc.stdout.splitlines()]
    return {r["id"]: r for r in replies if r["event"] == "result"}


def test_round_trip_over_stdio(tmp_path):
    (tmp_path / "a.pdf").write_text("x")
    results = run([
        {"id": 1, "method": "collect_paths", "params": {"paths": [str(tmp_path)]}},
        {"id": 2, "method": "youtube_plan",
         "params": {"url": f"https://youtu.be/{VIDEO}", "title": "My Talk",
                    "folder": str(tmp_path)}},
        {"id": 3, "method": "youtube_plan", "params": {"url": "https://example.com"}},
        {"id": 4, "method": "nope"},
        {"id": 5, "method": "environment_report", "params": {"deep": False}},
    ])
    assert results[1] == {"id": 1, "event": "result", "ok": True,
                          "data": [str(tmp_path / "a.pdf")]}
    assert results[2]["data"]["url"] == f"https://www.youtube.com/watch?v={VIDEO}"
    assert results[2]["data"]["output"] == str(tmp_path / "my-talk.md")
    assert results[3]["data"]["video_id"] is None and results[3]["data"]["error"]
    assert results[4]["ok"] is False
    assert results[5]["ok"] and "markitdown" in results[5]["data"]


def test_invalid_json_does_not_kill_the_process():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "sidecar.py")],
        input='not json\n{"id": 9, "method": "collect_paths", "params": {"paths": []}}\n',
        capture_output=True, text=True, timeout=60, cwd=ROOT,
    )
    replies = [json.loads(line) for line in proc.stdout.splitlines()]
    assert {"id": 9, "event": "result", "ok": True, "data": []} in replies


def test_log_lines_precede_the_single_result(monkeypatch):
    def noisy(log):
        log("one")
        log("two")
        return (True, "done")

    monkeypatch.setitem(sidecar.METHODS, "noisy",
                        lambda log: sidecar._outcome(noisy(log)))
    seen = []
    sidecar.handle({"id": 7, "method": "noisy"}, emit=seen.append)
    assert seen == [
        {"id": 7, "event": "log", "line": "one"},
        {"id": 7, "event": "log", "line": "two"},
        {"id": 7, "event": "result", "ok": True, "data": {"detail": "done"}},
    ]


def test_convert_writes_beside_the_source_when_no_output_is_given(monkeypatch, tmp_path):
    seen = {}

    def fake_convert(exe, source, output, expect_transcript=False):
        seen["output"] = output
        return (True, str(output))

    monkeypatch.setattr(sidecar.backend, "convert_file", fake_convert)
    source = tmp_path / "report.pdf"
    result = sidecar.convert_file(lambda line: None, "markitdown", str(source))
    assert seen["output"] == tmp_path / "report.md"
    assert result == {"detail": str(tmp_path / "report.md")}


def test_backend_failure_becomes_an_error_result(monkeypatch):
    monkeypatch.setitem(sidecar.METHODS, "boom",
                        lambda log: sidecar._outcome((False, "no network")))
    seen = []
    sidecar.handle({"id": 8, "method": "boom"}, emit=seen.append)
    assert seen == [{"id": 8, "event": "result", "ok": False, "error": "no network"}]
