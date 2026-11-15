# Contributing to tomd

Thanks for your interest! tomd is a thin GUI over [Microsoft MarkItDown](https://github.com/microsoft/markitdown) — issues and PRs welcome.

## Development setup

macOS. Requires [uv](https://docs.astral.sh/uv/), [bun](https://bun.sh/) and a [Rust toolchain](https://rustup.rs/).

```bash
git clone https://github.com/thekiwidev/tomd.git
cd tomd
uv sync
bun install
bun run tauri dev
```

The dev environment installs `markitdown[all]` so the app finds a CLI on PATH while you work. The packaged app never bundles it. A development build runs `sidecar.py` from the project's `.venv`; only the release build carries a frozen copy.

Checks before a pull request:

```bash
uv run pytest
bun run test
bun run typecheck
(cd src-tauri && cargo clippy && cargo test)
```

## Project layout

| File | Purpose |
|---|---|
| `src/` | The UI (React + TypeScript + Tailwind): main window, drop zone, status toast, settings, setup page; the conversion queue is `queue.ts` |
| `src-tauri/` | The desktop shell (Tauri v2, Rust): windows, menu bar icon, settings, drag watcher, Finder Quick Action, and the process that runs the sidecar |
| `sidecar.py` | JSON-lines front end to `backend.py` and `links.py`; the shell talks to it over stdin / stdout |
| `backend.py` | Device plumbing: env detection, markitdown resolution, setup install, subprocess conversion |
| `links.py` | Pure helpers: supported extensions, YouTube link parsing, output names |
| `tests/` | pytest for `links.py` and `sidecar.py` |
| `assets/icon.svg` | App icon source |
| `scripts/build_macos.sh` | Freezes the sidecar, builds the app, wraps it in a DMG |
| `docs/` | Landing page (GitHub Pages) |

## Ground rules

- **Never bundle MarkItDown into the app.** tomd runs the device's `markitdown` CLI; that's the architecture.
- UI icons come from `lucide-react` — no emoji glyphs, no icon image files.
- Conversion must stay sequential (one file at a time; the queue in `src/queue.ts`) and in the sidecar, never in the UI.
- Keep the app zero-config by default; new options belong behind settings.

## Building installers

```bash
bash scripts/build_macos.sh      # dist/tomd.app + dist/tomd.dmg
```

## Releases

Maintainers: bump `version` in `pyproject.toml`, `package.json`, `src-tauri/Cargo.toml` and `src-tauri/tauri.conf.json`, update `CHANGELOG.md`, then:

```bash
git tag vX.Y.Z && git push origin vX.Y.Z
```

GitHub Actions builds the macOS DMG and attaches it to a new release automatically. Windows stays on v0.1.11 until the Tauri app is built for it.
