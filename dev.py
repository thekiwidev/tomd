"""Hot-reload runner: restarts the app whenever app.py or backend.py change.

Usage:
    uv run python dev.py
"""

import subprocess
import sys
from pathlib import Path

from watchfiles import watch

WATCH = {"app.py", "backend.py"}


def run():
    return subprocess.Popen([sys.executable, "app.py"])


print("tomd dev — watching app.py and backend.py. Save to reload.\n")
proc = run()

for changes in watch(*[Path(f) for f in WATCH]):
    changed = {Path(p).name for _, p in changes}
    print(f"  ↺  {', '.join(sorted(changed))} changed — restarting…")
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
    proc = run()
