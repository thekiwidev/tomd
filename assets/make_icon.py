"""Render assets/icon.svg at all macOS sizes and emit tomd.iconset/.

Run with:  uv run python assets/make_icon.py
Then:      iconutil -c icns assets/tomd.iconset -o assets/tomd.icns
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

SVG_PATH = Path(__file__).parent / "icon.svg"


def render(renderer: QSvgRenderer, size: int) -> QImage:
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    # macOS icons keep a margin so the rounded square matches system icons.
    margin = size * 0.05
    renderer.render(painter, QRectF(margin, margin, size - 2 * margin, size - 2 * margin))
    painter.end()
    return image


def main():
    QGuiApplication(sys.argv)
    renderer = QSvgRenderer(str(SVG_PATH))
    out = Path(__file__).parent / "tomd.iconset"
    out.mkdir(exist_ok=True)
    for points in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            pixels = points * scale
            suffix = "" if scale == 1 else "@2x"
            render(renderer, pixels).save(str(out / f"icon_{points}x{points}{suffix}.png"))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
