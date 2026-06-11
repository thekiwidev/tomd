"""Render the tomd app icon at all macOS sizes and emit tomd.iconset/.

Run with:  uv run python assets/make_icon.py
Then:      iconutil -c icns assets/tomd.iconset -o assets/tomd.icns
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QLinearGradient, QPainter, QPainterPath, QGuiApplication


def render(size: int) -> QImage:
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)

    # macOS-style rounded square with a small margin
    margin = size * 0.06
    rect = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)
    radius = size * 0.21

    gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
    gradient.setColorAt(0.0, QColor("#7c6cf0"))
    gradient.setColorAt(1.0, QColor("#4b3bd1"))

    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    painter.fillPath(path, gradient)

    # "M↓" mark
    painter.setPen(QColor("white"))
    font = QFont("Helvetica Neue")
    font.setBold(True)
    font.setPixelSize(int(size * 0.46))
    painter.setFont(font)
    painter.drawText(rect.adjusted(0, -size * 0.04, 0, -size * 0.04), Qt.AlignCenter, "M↓")
    painter.end()
    return image


def main():
    QGuiApplication(sys.argv)
    out = Path(__file__).parent / "tomd.iconset"
    out.mkdir(exist_ok=True)
    for points in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            pixels = points * scale
            suffix = "" if scale == 1 else "@2x"
            render(pixels).save(str(out / f"icon_{points}x{points}{suffix}.png"))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
