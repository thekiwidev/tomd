# Build tomd.exe into dist\ on Windows.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

uv sync
uv run pyinstaller --noconfirm --onefile --windowed --name tomd app.py

Write-Host "Built dist\tomd.exe"
