#!/usr/bin/env bash
# Build tomd.app and a distributable tomd.dmg into dist/.
#
# Two parts: the Python sidecar (backend.py behind sidecar.py) frozen with
# PyInstaller, and the Tauri shell that carries it in its resources.
set -euo pipefail
cd "$(dirname "$0")/.."

uv sync
bun install --frozen-lockfile

# 1. The sidecar: a folder (starts faster than a one-file build, which unpacks
#    itself on every launch) at build/sidecar/tomd-sidecar/.
rm -rf build/sidecar
uv run pyinstaller --noconfirm --clean --onedir --console --name tomd-sidecar \
  --distpath build/sidecar --workpath build/pyinstaller --specpath build \
  sidecar.py

# 2. The app. The sidecar is added here rather than in tauri.conf.json so a
#    debug build, which runs sidecar.py from the venv, needs no frozen copy.
#    "-" signs ad hoc: tomd has no developer certificate, and Apple Silicon
#    refuses to run a bundle with no signature at all.
bun run tauri build --bundles app --config '{
  "bundle": {
    "resources": { "../build/sidecar/tomd-sidecar": "sidecar" },
    "macOS": { "signingIdentity": "-" }
  }
}'
APP="src-tauri/target/release/bundle/macos/tomd.app"

# 3. Stage the app beside an /Applications shortcut and wrap it in a DMG.
mkdir -p dist
rm -rf dist/tomd.app dist/tomd.dmg
ditto "$APP" dist/tomd.app
STAGING="$(mktemp -d)"
ditto dist/tomd.app "$STAGING/tomd.app"
ln -s /Applications "$STAGING/Applications"
hdiutil create -volname tomd -srcfolder "$STAGING" -ov -format UDZO dist/tomd.dmg
rm -rf "$STAGING"

echo "Built dist/tomd.app and dist/tomd.dmg"
du -sh dist/tomd.app dist/tomd.dmg
