# Contributing to tomd

Thanks for your interest! tomd is a thin GUI over [Microsoft MarkItDown](https://github.com/microsoft/markitdown) — issues and PRs welcome.

## Development setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/thekiwidev/tomd.git
cd tomd
uv sync
uv run python app.py
```

The dev environment installs `markitdown[all]` so the app finds a CLI on PATH while you work. The packaged app never bundles it.

## Project layout

| File | Purpose |
|---|---|
| `app.py` | The whole GUI (PySide6): setup page, drop zone, queue, rows, toasts |
| `backend.py` | Device plumbing: env detection, markitdown resolution, setup install, subprocess conversion |
| `assets/icon.svg` | App icon source; `assets/make_icon.py` renders the macOS iconset |
| `scripts/` | Local build scripts for macOS (.app/.dmg) and Windows (.exe) |
| `docs/` | Landing page (GitHub Pages) |

## Ground rules

- **Never bundle MarkItDown into the app.** tomd runs the device's `markitdown` CLI; that's the architecture.
- UI icons are inline Lucide SVG paths in `ICON_PATHS` — no emoji glyphs, no icon image files.
- Conversion must stay sequential (one subprocess at a time) and off the UI thread.
- Keep the app zero-config by default; new options belong behind settings.

## Building installers

```bash
bash scripts/build_macos.sh      # dist/tomd.app + dist/tomd.dmg
pwsh scripts/build_windows.ps1   # dist\tomd.exe
```

## Releases

Maintainers: bump `version` in `pyproject.toml`, update `CHANGELOG.md`, then:

```bash
git tag vX.Y.Z && git push origin vX.Y.Z
```

GitHub Actions builds the macOS DMG and Windows EXE and attaches them to a new release automatically.
