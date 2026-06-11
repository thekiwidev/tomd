#!/usr/bin/env bash
# Build tomd.app and a distributable tomd.dmg into dist/.
set -euo pipefail
cd "$(dirname "$0")/.."

uv sync
uv run python assets/make_icon.py
iconutil -c icns assets/tomd.iconset -o assets/tomd.icns

uv run pyinstaller --noconfirm --windowed --name tomd \
  --icon assets/tomd.icns \
  --collect-data markitdown \
  --osx-bundle-identifier dev.thekiwidev.tomd \
  app.py

# Stage a folder with the app and an /Applications shortcut, then wrap in a DMG.
STAGING="$(mktemp -d)"
cp -R dist/tomd.app "$STAGING/"
ln -s /Applications "$STAGING/Applications"
rm -f dist/tomd.dmg
hdiutil create -volname tomd -srcfolder "$STAGING" -ov -format UDZO dist/tomd.dmg
rm -rf "$STAGING"

echo "Built dist/tomd.app and dist/tomd.dmg"
