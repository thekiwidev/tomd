"""tomd — drag & drop anything, get Markdown.

A thin GUI over the `markitdown` CLI by Microsoft
(https://github.com/microsoft/markitdown). The app does no conversion
itself: it runs the markitdown installed on this device, exactly as you
would in a terminal. On first launch it checks the device for the
requirements and offers to install them into a private environment.
"""

import queue
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import (
    QByteArray,
    QMimeData,
    QPoint,
    QRect,
    QSettings,
    QSize,
    Qt,
    QThread,
    QTimer,
    QUrl,
    Signal,
)
from PySide6.QtGui import (
    QAction,
    QDrag,
    QGuiApplication,
    QIcon,
    QKeySequence,
    QPainter,
    QPixmap,
    QShortcut,
    QTransform,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedLayout,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

import backend
import native

APP_NAME = "tomd"

# Extensions MarkItDown can handle. Used to filter folder drops; a file
# dropped directly is always accepted so MarkItDown can have a go at it.
SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".csv",
    ".json", ".xml", ".html", ".htm", ".txt", ".rtf", ".epub", ".msg",
    ".eml", ".wav", ".mp3", ".m4a", ".jpg", ".jpeg", ".png", ".webp",
    ".ipynb", ".zip",
}

PENDING, QUEUED, RUNNING, DONE, ERROR = range(5)

# Theme palette, shared between the stylesheet and tinted icons.
COLOR_TEXT = "#e8e9ee"
COLOR_MUTED = "#8b8e98"
COLOR_ACCENT = "#7c6cf0"
COLOR_GREEN = "#7ddc9a"
COLOR_AMBER = "#e6c468"
COLOR_RED = "#e07a7f"

STYLE = f"""
* {{ font-family: "Inter", -apple-system, "SF Pro Text", "Segoe UI", sans-serif; }}
QMainWindow, #centralWidget, #mainPage, #setupPage {{ background: #15161a; }}
#titleLabel {{ font-family: "Space Grotesk", "Inter", -apple-system, sans-serif; color: #f2f3f7; font-size: 24px; font-weight: 500; letter-spacing: 0.015em; }}
#subtitleLabel {{ color: {COLOR_MUTED}; font-size: 13px; }}
#dropHint {{
    border: 2px dashed #34363f; border-radius: 14px;
    background: #1a1b20;
}}
#dropHint[dragOver="true"] {{ border-color: {COLOR_ACCENT}; background: #1e1d2b; }}
#dropHint QLabel {{ color: {COLOR_MUTED}; font-size: 15px; }}
#dropHint[dragOver="true"] QLabel {{ color: #b9b0fa; }}
#fileScroll {{ border: none; background: transparent; }}
#fileListContainer {{ background: transparent; }}
#fileRow {{ background: #1e1f26; border-radius: 10px; }}
#fileRow[state="done"] {{ background: #1c2420; }}
#fileRow[state="error"] {{ background: #261d1e; }}
#fileRow[selected="true"] {{ background: #252040; border: 1px solid {COLOR_ACCENT}; }}
#fileRow[selected="true"][state="done"] {{ background: #1e2e28; border: 1px solid {COLOR_ACCENT}; }}
#fileName {{ color: {COLOR_TEXT}; font-size: 13px; font-weight: 600; }}
#fileSub {{ font-family: "JetBrains Mono", ui-monospace, Menlo, Consolas, monospace; color: #7f828d; font-size: 11px; }}
#fileSub[state="error"] {{ color: {COLOR_RED}; }}
QPushButton {{
    background: #2a2c35; color: #d6d8e0; border: none;
    border-radius: 8px; padding: 6px 14px; font-size: 12px; font-weight: 500;
}}
QPushButton:hover {{ background: #343742; }}
QPushButton:pressed {{ background: #3d404d; }}
QPushButton:disabled {{ background: #22232a; color: #565963; }}
QPushButton#runButton, QPushButton#installButton {{
    background: #6c5ce7; color: white; font-size: 13px; padding: 9px 22px;
}}
QPushButton#runButton:hover, QPushButton#installButton:hover {{ background: {COLOR_ACCENT}; }}
QPushButton#runButton:disabled, QPushButton#installButton:disabled {{ background: #3a3554; color: #837fa6; }}
#dragChip {{
    font-family: "JetBrains Mono", ui-monospace, Menlo, Consolas, monospace;
    color: #9fe0b8; background: #2a3d33; border-radius: 8px;
    padding: 4px 10px; font-size: 11px; font-weight: 600;
}}
#dragChip:hover {{ background: #345043; }}
#countLabel {{ font-family: "JetBrains Mono", ui-monospace, Menlo, Consolas, monospace; color: {COLOR_MUTED}; font-size: 12px; }}
#envLabel {{ font-family: "JetBrains Mono", ui-monospace, Menlo, Consolas, monospace; color: {COLOR_MUTED}; font-size: 10px; }}
QCheckBox {{ color: #b6b9c2; font-size: 12px; spacing: 6px; }}
QCheckBox::indicator {{
    width: 15px; height: 15px; border-radius: 4px;
    border: 1px solid #444752; background: #22232a;
}}
QCheckBox::indicator:checked {{ background: #6c5ce7; border-color: #6c5ce7; }}
QProgressBar {{
    background: #22232a; border: none; border-radius: 3px;
    min-height: 6px; max-height: 6px;
}}
QProgressBar::chunk {{ background: #6c5ce7; border-radius: 3px; }}
#toast {{
    color: {COLOR_TEXT}; background: #2a2c35; border-radius: 10px;
    padding: 10px 18px; font-size: 12px; font-weight: 600;
}}
#toast[kind="error"] {{ background: #4a2a2e; color: #f0b6ba; }}
#toast[kind="success"] {{ background: #24402f; color: #a5e6bd; }}
#setupHeading {{ color: #f2f3f7; font-size: 20px; font-weight: 700; }}
#setupBody {{ color: #b6b9c2; font-size: 13px; }}
#checkItem {{ color: #b6b9c2; font-size: 13px; }}
#setupLog {{
    background: #101114; color: #9da1ab; border: 1px solid #26272e;
    border-radius: 10px; font-family: "JetBrains Mono", Menlo, Consolas, monospace; font-size: 11px;
    padding: 6px;
}}
QScrollBar:vertical {{ background: transparent; width: 8px; }}
QScrollBar::handle:vertical {{ background: #34363f; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
"""

# ---------------------------------------------------------------------------
# Inline SVG icons (Lucide outlines), tinted at render time with theme colors.
# ---------------------------------------------------------------------------

ICON_PATHS = {
    "arrow-down-to-line": '<path d="M12 17V3"/><path d="m6 11 6 6 6-6"/><path d="M19 21H5"/>',
    "refresh": (
        '<path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>'
        '<path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/><path d="M16 16h5v5"/>'
    ),
    "square": '<rect width="18" height="18" x="3" y="3" rx="2"/>',
    "hash": (
        '<line x1="4" x2="20" y1="9" y2="9"/><line x1="4" x2="20" y1="15" y2="15"/>'
        '<line x1="10" x2="8" y1="3" y2="21"/><line x1="16" x2="14" y1="3" y2="21"/>'
    ),
    "circle": '<circle cx="12" cy="12" r="9"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "loader": '<path d="M21 12a9 9 0 1 1-6.219-8.56"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "grip": (
        '<circle cx="12" cy="5" r="1"/><circle cx="19" cy="5" r="1"/><circle cx="5" cy="5" r="1"/>'
        '<circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>'
        '<circle cx="12" cy="19" r="1"/><circle cx="19" cy="19" r="1"/><circle cx="5" cy="19" r="1"/>'
    ),
    "copy": (
        '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>'
        '<path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>'
    ),
    "folder": (
        '<path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9'
        'l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z"/>'
        '<circle cx="12" cy="13" r="1"/>'
    ),
    "plus": '<path d="M5 12h14"/><path d="M12 5v14"/>',
    "trash": (
        '<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M3 6h18"/>'
        '<path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>'
    ),
    "terminal": '<path d="m4 17 6-6-6-6"/><path d="M12 19h8"/>',
    "file": (
        '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>'
        '<path d="M14 2v4a2 2 0 0 0 2 2h4"/>'
    ),
    "settings": (
        '<path d="M20 7h-9"/><path d="M14 17H5"/>'
        '<circle cx="17" cy="17" r="3"/><circle cx="7" cy="7" r="3"/>'
    ),
}


def icon_pixmap(name: str, color: str, size: int = 16, filled: bool = False) -> QPixmap:
    fill = color if filled else "none"
    stroke = "none" if filled else color
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f"{ICON_PATHS[name]}</svg>"
    )
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return pixmap


def themed_icon(name: str, color: str, size: int = 16, filled: bool = False) -> QIcon:
    return QIcon(icon_pixmap(name, color, size, filled))


# The two glyphs from assets/icon.svg — the # and the downward return arrow —
# so the menu-bar icon matches the desktop app icon. Rendered in any colour.
_APP_GLYPH_HASH = (
    "M117.9 371L129 311H103.5V291.5H132.6L143.4 231.5H114V212H147L158.1 152H179.1"
    "L168 212H216L227.1 152H248.1L237 212H262.5V231.5H233.4L222.6 291.5H252V311H219"
    "L207.9 371H186.9L198 311H150L138.9 371H117.9ZM153.6 291.5H201.6L212.4 231.5H164.4"
    "L153.6 291.5Z"
)
_APP_GLYPH_ARROW = (
    "M369.689 355.796L362.093 363.398L369.689 371L377.284 363.398L369.689 355.796Z"
    "M283.743 173C280.894 173 278.161 174.133 276.147 176.149C274.132 178.166 273 180.901"
    " 273 183.753C273 186.604 274.132 189.339 276.147 191.356C278.161 193.373 280.894"
    " 194.505 283.743 194.505V173ZM308.377 309.634L362.093 363.398L377.284 348.194L323.568"
    " 294.43L308.377 309.634ZM377.284 363.398L431 309.634L415.809 294.43L362.093 348.194"
    "L377.284 363.398ZM380.432 355.796V248.269H358.945V355.796H380.432ZM305.23 173H283.743"
    "V194.505H305.23V173ZM380.432 248.269C380.432 228.306 372.509 209.161 358.406 195.046"
    "C344.302 180.93 325.174 173 305.23 173V194.505C319.476 194.505 333.139 200.17 343.212"
    " 210.252C353.286 220.335 358.945 234.01 358.945 248.269H380.432Z"
)


def app_logo_pixmap(color: str, size: int = 18) -> QPixmap:
    # Tight square viewBox cropped around the two glyphs so they fill the icon
    # (the full 525×525 art has a lot of empty margin, making it look tiny).
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="97 92 340 340">'
        f'<path d="{_APP_GLYPH_HASH}" fill="{color}"/>'
        f'<path d="{_APP_GLYPH_ARROW}" fill="{color}"/></svg>'
    )
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return pixmap


def app_logo_icon(color: str, size: int = 18) -> QIcon:
    return QIcon(app_logo_pixmap(color, size))


def collect_paths(urls):
    """Expand dropped URLs into a flat list of convertible file paths."""
    files = []
    for url in urls:
        path = Path(url.toLocalFile())
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_file() and child.suffix.lower() in SUPPORTED_EXTENSIONS:
                    files.append(child)
    return files


def reveal_in_file_manager(path: Path):
    if sys.platform == "darwin":
        subprocess.Popen(["open", "-R", str(path)])
    elif sys.platform == "win32":
        subprocess.Popen(["explorer", "/select,", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path.parent)])


DOCK_ANCHORS = (
    "top-left", "top-right", "bottom-left",
    "bottom-right", "left-center", "right-center",
)
DOCK_ANCHOR_LABELS = {
    "top-left": "Top left",
    "top-right": "Top right",
    "bottom-left": "Bottom left",
    "bottom-right": "Bottom right",
    "left-center": "Left center",
    "right-center": "Right center",
}


def dock_geometry(anchor: str, screen: QRect, size: QSize, margin: int = 14) -> QRect:
    """Where a dock of `size` sits for `anchor` within a screen's available
    rect, inset by `margin`. Pure geometry — no widgets — so it's unit-checkable.
    The result is clamped to stay fully inside `screen`."""
    w, h = size.width(), size.height()
    left = screen.left() + margin
    right = screen.right() - w - margin + 1
    top = screen.top() + margin
    bottom = screen.bottom() - h - margin + 1
    mid_y = screen.top() + (screen.height() - h) // 2
    coords = {
        "top-left": (left, top),
        "top-right": (right, top),
        "bottom-left": (left, bottom),
        "bottom-right": (right, bottom),
        "left-center": (left, mid_y),
        "right-center": (right, mid_y),
    }
    x, y = coords.get(anchor, coords["bottom-right"])
    # Clamp so a dock larger than the screen (or odd margins) never spills off.
    x = max(screen.left(), min(x, screen.right() - w + 1))
    y = max(screen.top(), min(y, screen.bottom() - h + 1))
    return QRect(x, y, w, h)


class QueueWorker(QThread):
    """Sequential conversion queue. One markitdown subprocess at a time."""

    job_started = Signal(object)
    job_done = Signal(object, str)
    job_failed = Signal(object, str)

    def __init__(self, markitdown_exe: str, parent=None):
        super().__init__(parent)
        self.markitdown_exe = markitdown_exe
        self._queue = queue.Queue()

    def enqueue(self, row):
        self._queue.put(row)

    def clear_pending(self):
        """Drain not-yet-started jobs; returns the rows that were dequeued."""
        drained = []
        try:
            while True:
                item = self._queue.get_nowait()
                if item is not None:
                    drained.append(item)
        except queue.Empty:
            pass
        return drained

    def stop(self):
        self._queue.put(None)

    def run(self):
        while True:
            row = self._queue.get()
            if row is None:
                break
            self.job_started.emit(row)
            ok, detail = backend.convert_file(self.markitdown_exe, row.source)
            (self.job_done if ok else self.job_failed).emit(row, detail)


class SetupWorker(QThread):
    """Installs markitdown[all] into tomd's private environment."""

    log_line = Signal(str)
    finished_setup = Signal(bool, str)

    def run(self):
        ok, error = backend.install_markitdown(self.log_line.emit)
        self.finished_setup.emit(ok, error)


class HomebrewSetupWorker(QThread):
    """Installs a system Python via Homebrew — the explicit alternative to
    the automatic uv bootstrap in SetupWorker."""

    log_line = Signal(str)
    finished_setup = Signal(bool, str)

    def run(self):
        ok, error = backend.install_homebrew_python(self.log_line.emit)
        self.finished_setup.emit(ok, error)


class Toast(QLabel):
    """Transient notification pinned to the bottom of the window."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAlignment(Qt.AlignCenter)
        self.hide()
        self._timer = QTimer(self, singleShot=True, timeout=self.hide)

    def show_message(self, text: str, kind: str = "info", duration_ms: int = 4000):
        self.setProperty("kind", kind)
        self.style().unpolish(self)
        self.style().polish(self)
        self.setText(text)
        self.adjustSize()
        self.reposition()
        self.show()
        self.raise_()
        self._timer.start(duration_ms)

    def reposition(self):
        parent = self.parentWidget()
        if parent:
            self.move((parent.width() - self.width()) // 2, parent.height() - self.height() - 66)


class RowChip(QWidget):
    """Base chip widget — same visual spec as drag .md: identical layout, font, padding."""

    _CHIP_COLOR = "#9fe0b8"
    _CHIP_ICON_SIZE = 12
    _CHIP_ICON_BOX  = 14

    def __init__(self, icon_name: str, label: str, parent=None):
        super().__init__(parent)
        self.setObjectName("dragChip")          # reuse the single shared stylesheet rule
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_Hover, True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(5)
        self._icon_lbl = QLabel()
        self._icon_lbl.setFixedSize(self._CHIP_ICON_BOX, self._CHIP_ICON_BOX)
        self._icon_lbl.setAlignment(Qt.AlignCenter)
        self._icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._text_lbl = QLabel(label)
        self._text_lbl.setStyleSheet(
            f'color: {self._CHIP_COLOR}; '
            'font-family: "Inter", -apple-system, "SF Pro Text", "Segoe UI", sans-serif; '
            'font-size: 11px; font-weight: 600; background: transparent;'
        )
        self._text_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(self._icon_lbl)
        layout.addWidget(self._text_lbl)
        self._set_icon(icon_name)

    def _set_icon(self, name: str):
        self._icon_lbl.setPixmap(icon_pixmap(name, self._CHIP_COLOR, self._CHIP_ICON_SIZE))

    def set_content(self, icon_name: str, label: str):
        self._set_icon(icon_name)
        self._text_lbl.setText(label)

    def set_text_visible(self, visible: bool):
        """Show/hide the chip label (icon-only mode for narrow windows)."""
        self._text_lbl.setVisible(visible)


class ActionChip(RowChip):
    """Clickable RowChip — same look as drag .md but fires a signal on click."""

    clicked = Signal()

    def __init__(self, icon_name: str, label: str, parent=None):
        super().__init__(icon_name, label, parent)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()


class DragChip(RowChip):
    """RowChip that initiates a file drag instead of emitting a click signal."""

    def __init__(self, parent=None):
        super().__init__("grip", "drag .md", parent)
        self.md_path = None
        self._press_pos = None
        self.setCursor(Qt.OpenHandCursor)
        self.setToolTip("Drag this into Finder, an editor, or anywhere that accepts files")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_pos = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)

    def mouseMoveEvent(self, event):
        if self.md_path is None or self._press_pos is None:
            return
        if (event.position().toPoint() - self._press_pos).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(self.md_path))])
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)
        self.setCursor(Qt.OpenHandCursor)


class SelectBox(QLabel):
    """Small checkbox-style toggle that lives at the left edge of a FileRow."""

    toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self.setFixedSize(18, 18)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.PointingHandCursor)
        self._refresh()

    def _refresh(self):
        if self._checked:
            self.setPixmap(icon_pixmap("check", COLOR_ACCENT, 11, filled=False))
            self.setStyleSheet(
                "background: #3a3070; border: 1.5px solid #7c6cf0; border-radius: 4px;"
            )
        else:
            self.setPixmap(QPixmap())
            self.setStyleSheet(
                "background: #22232a; border: 1.5px solid #444752; border-radius: 4px;"
            )

    @property
    def checked(self):
        return self._checked

    def set_checked(self, value: bool):
        if self._checked == value:
            return
        self._checked = value
        self._refresh()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._checked = not self._checked
            self._refresh()
            self.toggled.emit(self._checked)


class FileRow(QFrame):
    selection_changed = Signal(object)  # emits self

    _NAME_MIN_WIDTH = 60  # px — name/sub never shrink below this before eliding

    STATUS = {
        PENDING: ("circle", COLOR_MUTED),
        QUEUED: ("clock", COLOR_MUTED),
        RUNNING: ("loader", COLOR_AMBER),
        DONE: ("check", COLOR_GREEN),
        ERROR: ("x", COLOR_RED),
    }

    def __init__(self, source: Path, parent=None):
        super().__init__(parent)
        self.setObjectName("fileRow")
        self.source = source
        self.md_path = None
        self.state = PENDING
        self.selected = False
        self._spin_angle = 0
        self._spin_timer = QTimer(self, interval=80, timeout=self._spin)
        self._loader_pixmap = icon_pixmap("loader", COLOR_AMBER, 11)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        self.select_box = SelectBox()
        self.select_box.toggled.connect(lambda checked: self.set_selected(checked))
        layout.addWidget(self.select_box)

        self.status_label = QLabel()
        self.status_label.setFixedSize(16, 16)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setPixmap(icon_pixmap("circle", COLOR_MUTED, 11))
        layout.addWidget(self.status_label)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        self._full_name = source.name
        self._full_sub = ""
        self.name_label = QLabel(source.name)
        self.name_label.setObjectName("fileName")
        self.name_label.setToolTip(source.name)
        # The name column flexes with the window: it takes the leftover space
        # (so it's long on a wide window) but can shrink all the way down to
        # _NAME_MIN_WIDTH, middle-elided in _elide_labels(), so the action chips
        # are never pushed off the row. Ignored policy lets it shrink past its
        # text width; the minimum keeps the name from vanishing entirely.
        self.name_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.name_label.setMinimumWidth(self._NAME_MIN_WIDTH)

        # Sub row: file icon initially, replaced by text on status changes.
        sub_row = QHBoxLayout()
        sub_row.setSpacing(4)
        sub_row.setContentsMargins(0, 0, 0, 0)
        self._sub_icon = QLabel()
        self._sub_icon.setPixmap(icon_pixmap("file", COLOR_MUTED, 10))
        self._sub_icon.setFixedSize(12, 12)
        self._sub_icon.setAlignment(Qt.AlignCenter)
        self.sub_label = QLabel()
        self.sub_label.setObjectName("fileSub")
        # Same flex behaviour as the name so a long "→ output.md" also truncates
        # instead of widening the row and forcing a horizontal scrollbar.
        self.sub_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.sub_label.setMinimumWidth(self._NAME_MIN_WIDTH)
        self.sub_label.hide()
        sub_row.addWidget(self._sub_icon)
        sub_row.addWidget(self.sub_label, stretch=1)

        text_col.addWidget(self.name_label)
        text_col.addLayout(sub_row)
        layout.addLayout(text_col, stretch=1)

        self.copy_button = ActionChip("copy", "Copy MD")
        self.copy_button.setToolTip("Copy the markdown content to the clipboard")
        self.copy_button.clicked.connect(self.copy_markdown)

        self.drag_chip = DragChip()

        self.reveal_button = ActionChip("folder", "Reveal")
        self.reveal_button.setToolTip("Show the .md file in Finder")
        self.reveal_button.clicked.connect(self.reveal)

        self.more_button = ActionChip("hash", "•••")
        self.more_button.setToolTip("More actions")
        self.more_button.clicked.connect(self._show_more_menu)
        self.more_button.hide()

        for widget in (self.copy_button, self.drag_chip, self.reveal_button, self.more_button):
            layout.addWidget(widget)
            widget.hide()

        self._action_widgets = [self.copy_button, self.drag_chip, self.reveal_button]

    def _show_more_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu { background: #1e1f26; border: 1px solid #34363f; border-radius: 8px; padding: 4px; }"
            "QMenu::item { color: #d6d8e0; padding: 7px 16px; font-size: 12px; border-radius: 5px; }"
            "QMenu::item:selected { background: #2a2c35; }"
        )
        copy_act = menu.addAction("Copy MD")
        copy_act.triggered.connect(self.copy_markdown)
        if self.md_path:
            reveal_act = menu.addAction("Reveal in Finder")
            reveal_act.triggered.connect(self.reveal)
        menu.exec(self.more_button.mapToGlobal(self.more_button.rect().bottomLeft()))

    def contextMenuEvent(self, event):
        if self.state == DONE:
            self._show_more_menu()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.state == DONE:
            self._update_action_layout()
        self._elide_labels()

    def _elide_labels(self):
        """Middle-elide the filename and the sub-line to whatever width the
        layout currently gives them, so the extension stays visible and neither
        line ever widens the row past the window (no horizontal scrollbar)."""
        fm = self.name_label.fontMetrics()
        self.name_label.setText(
            fm.elidedText(self._full_name, Qt.ElideMiddle, max(self.name_label.width(), 0))
        )
        if self._full_sub:
            sfm = self.sub_label.fontMetrics()
            self.sub_label.setText(
                sfm.elidedText(self._full_sub, Qt.ElideMiddle, max(self.sub_label.width(), 0))
            )

    def _update_action_layout(self):
        # Action chips are always shown once a row is DONE; when the window is
        # narrower than 560 px they drop their text and show icon-only
        # (tooltips carry the label). Gauge the *window* width, not the row's,
        # so the breakpoint matches what the user sees.
        expanded = self.window().width() >= 560
        for w in self._action_widgets:
            w.setVisible(True)
            w.set_text_visible(expanded)
        self.more_button.setVisible(False)

    def set_selected(self, value: bool):
        self.selected = value
        self.select_box.set_checked(value)
        self.setProperty("selected", "true" if value else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self.selection_changed.emit(self)

    def _spin(self):
        self._spin_angle = (self._spin_angle + 30) % 360
        dpr = self._loader_pixmap.devicePixelRatio()
        phys = self._loader_pixmap.width()          # physical px (logical * dpr)
        log  = phys / dpr                           # logical px
        canvas = QPixmap(phys, phys)
        canvas.fill(Qt.transparent)
        canvas.setDevicePixelRatio(dpr)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(log / 2, log / 2)
        painter.rotate(self._spin_angle)
        painter.translate(-log / 2, -log / 2)
        painter.drawPixmap(0, 0, self._loader_pixmap)
        painter.end()
        self.status_label.setPixmap(canvas)

    def _show_sub_text(self, text: str):
        self._sub_icon.hide()
        self._full_sub = text
        self.sub_label.setToolTip(text)
        self.sub_label.setText(text)
        self.sub_label.show()
        self._elide_labels()

    def _show_sub_icon(self):
        self._full_sub = ""
        self.sub_label.hide()
        self._sub_icon.show()

    def set_state(self, state, detail=None):
        self.state = state
        icon_name, color = self.STATUS[state]
        if state == RUNNING:
            self._spin_timer.start()
        else:
            self._spin_timer.stop()
            self.status_label.setPixmap(icon_pixmap(icon_name, color, 11))
        self.setProperty("state", {DONE: "done", ERROR: "error"}.get(state, ""))
        self.sub_label.setProperty("state", "error" if state == ERROR else "")
        if state == QUEUED:
            self._show_sub_text("Queued…")
        elif state == RUNNING:
            self._show_sub_text("Converting…")
        elif state == DONE:
            self.md_path = Path(detail)
            self.drag_chip.md_path = self.md_path
            self._show_sub_text(f"→ {self.md_path.name}")
            self._update_action_layout()
        elif state == ERROR:
            self._show_sub_text(detail or "Conversion failed")
            self.sub_label.setToolTip(detail or "")
        else:
            self._show_sub_icon()
        for widget in (self, self.sub_label):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def copy_markdown(self):
        if self.md_path and self.md_path.exists():
            QGuiApplication.clipboard().setText(self.md_path.read_text(encoding="utf-8"))
            self.copy_button.set_content("check", "Copied")
            QTimer.singleShot(1500, self._reset_copy_button)

    def _reset_copy_button(self):
        self.copy_button.set_content("copy", "Copy MD")

    def reveal(self):
        if self.md_path:
            reveal_in_file_manager(self.md_path)


class SetupPage(QWidget):
    """First-run screen: shows what the device is missing and installs it."""

    setup_complete = Signal(str)  # path to the markitdown executable

    def __init__(self, report: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("setupPage")
        self.worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(12)

        heading = QLabel("One-time setup")
        heading.setObjectName("setupHeading")
        body = QLabel(
            "tomd is a GUI for Microsoft's MarkItDown — the conversion runs on "
            "your device, not inside this app. MarkItDown wasn't found, so tomd "
            "will install it into a private environment at:\n"
            f"{backend.managed_venv_dir()}"
        )
        body.setObjectName("setupBody")
        body.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(body)

        self.check_labels = {}
        for key, label_text in (
            ("python", "Python 3.10+"),
            ("uv", "uv (optional, used if present)"),
            ("markitdown", "markitdown CLI"),
        ):
            row = QHBoxLayout()
            icon_label = QLabel()
            icon_label.setFixedSize(18, 18)
            text_label = QLabel(label_text)
            text_label.setObjectName("checkItem")
            row.addWidget(icon_label)
            row.addWidget(text_label)
            row.addStretch()
            layout.addLayout(row)
            self.check_labels[key] = (icon_label, text_label)

        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("setupLog")
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("Setup output will appear here…")
        layout.addWidget(self.log_view, stretch=1)

        button_row = QHBoxLayout()
        self.recheck_button = QPushButton("Re-check")
        self.recheck_button.clicked.connect(self.recheck)
        self.install_button = QPushButton("Install MarkItDown")
        self.install_button.setObjectName("installButton")
        self.install_button.setIcon(themed_icon("terminal", "white", 13))
        self.install_button.setToolTip(
            "Installs uv (if needed) and markitdown automatically — no Python required beforehand."
        )
        self.install_button.clicked.connect(self.start_install)
        button_row.addWidget(self.recheck_button)
        button_row.addStretch()
        button_row.addWidget(self.install_button)
        layout.addLayout(button_row)

        # Secondary, explicit path for anyone who'd rather have a real
        # system-wide Python via Homebrew instead of tomd's uv-managed one.
        homebrew_row = QHBoxLayout()
        self.homebrew_button = QPushButton("Install Python via Homebrew instead")
        self.homebrew_button.clicked.connect(self.start_homebrew_install)
        homebrew_row.addStretch()
        homebrew_row.addWidget(self.homebrew_button)
        layout.addLayout(homebrew_row)

        self.update_checks(report)

    def update_checks(self, report: dict):
        def mark(key, present, text):
            icon_label, text_label = self.check_labels[key]
            name, color = ("check", COLOR_GREEN) if present else ("x", COLOR_RED)
            icon_label.setPixmap(icon_pixmap(name, color, 13))
            text_label.setText(text)

        python_text = "Python 3.10+"
        if report["python"]:
            python_text += f" — found {report['python_version']} at {report['python']}"
        else:
            python_text += " — not found"
        mark("python", bool(report["python"]), python_text)
        mark("uv", bool(report["uv"]), f"uv — {report['uv'] or 'not found (optional)'}")
        mark("markitdown", bool(report["markitdown"]), f"markitdown CLI — {report['markitdown'] or 'not installed'}")
        # Install can now bootstrap uv itself, so it's actionable even when
        # nothing has been detected yet — only a completed install disables it.
        self.install_button.setEnabled(not report["markitdown"])

    def recheck(self):
        report = backend.environment_report()
        self.update_checks(report)
        if report["markitdown"]:
            self.setup_complete.emit(report["markitdown"])

    def start_install(self):
        self.install_button.setEnabled(False)
        self.homebrew_button.setEnabled(False)
        self.recheck_button.setEnabled(False)
        self.log_view.clear()
        self.worker = SetupWorker(self)
        self.worker.log_line.connect(self.append_log)
        self.worker.finished_setup.connect(self.on_finished)
        self.worker.start()

    def start_homebrew_install(self):
        self.install_button.setEnabled(False)
        self.homebrew_button.setEnabled(False)
        self.recheck_button.setEnabled(False)
        self.log_view.clear()
        self.worker = HomebrewSetupWorker(self)
        self.worker.log_line.connect(self.append_log)
        self.worker.finished_setup.connect(self.on_homebrew_finished)
        self.worker.start()

    def append_log(self, line: str):
        self.log_view.appendPlainText(line)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

    def on_finished(self, ok: bool, error: str):
        self.recheck_button.setEnabled(True)
        self.homebrew_button.setEnabled(True)
        if ok:
            self.append_log("✓ Setup complete.")
            self.setup_complete.emit(str(backend.venv_executable("markitdown")))
        else:
            self.append_log(f"Setup failed: {error}")
            self.install_button.setEnabled(True)

    def on_homebrew_finished(self, ok: bool, error: str):
        self.recheck_button.setEnabled(True)
        self.install_button.setEnabled(True)
        self.homebrew_button.setEnabled(True)
        if ok:
            self.append_log("✓ Python installed via Homebrew.")
            self.recheck()
        elif error == "HOMEBREW_MISSING":
            self.append_log(
                "Homebrew isn't installed. Paste this into Terminal, then click "
                "Re-check:\n"
                '/bin/bash -c "$(curl -fsSL '
                "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            )
        else:
            self.append_log(f"Homebrew install failed: {error}")


class MainPage(QWidget):
    """The converter UI: drop zone, queue, progress, actions. Also acts as the
    shared controller: the dock feeds files in here and listens to these relay
    signals so both views share one conversion queue."""

    row_converted = Signal(object, str)   # (FileRow, md_path)
    row_failed = Signal(object, str)      # (FileRow, error)
    cleared = Signal()                    # list emptied — dock mirrors it

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.setObjectName("mainPage")
        self.window = window
        self.rows = []
        self.worker = None
        self.markitdown_exe = None
        self.batch_total = 0
        self.batch_done = 0
        self.settings = QSettings("thekiwidev", "tomd")

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(12)

        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_row = QHBoxLayout()
        title_row.setSpacing(7)
        logo = QLabel()
        logo.setPixmap(icon_pixmap("hash", COLOR_ACCENT, 20))
        title = QLabel("tomd")
        title.setObjectName("titleLabel")
        title_row.addWidget(logo)
        title_row.addWidget(title)
        title_row.addStretch()
        subtitle = QLabel("Drop files or folders anywhere in this window.")
        subtitle.setObjectName("subtitleLabel")
        title_col.addLayout(title_row)
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()
        # The auto-convert toggle lives in Settings + the menu bar now, not in
        # the window view. The checkbox is kept (hidden) as the shared state.
        self.auto_convert = QCheckBox("Auto-convert on drop", self)
        self.auto_convert.setChecked(self.settings.value("auto_convert_on_drop", False, type=bool))
        self.auto_convert.toggled.connect(lambda v: self.settings.setValue("auto_convert_on_drop", v))
        self.auto_convert.hide()
        self.settings_button = QPushButton()
        self.settings_button.setIcon(themed_icon("settings", "#d6d8e0", 15))
        self.settings_button.setToolTip("Settings (⌘,)")
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.setFixedSize(28, 28)
        self.settings_button.setStyleSheet(
            "QPushButton { background: transparent; border: none; border-radius: 7px; }"
            "QPushButton:hover { background: #23252e; }"
        )
        self.settings_button.clicked.connect(self.open_settings)
        header.addWidget(self.settings_button, alignment=Qt.AlignTop)
        root.addLayout(header)

        # Stacked area: big drop hint when empty, file list once populated.
        self.stack = QStackedLayout()
        root.addLayout(self.stack, stretch=1)

        self.drop_hint = QFrame()
        self.drop_hint.setObjectName("dropHint")
        hint_layout = QVBoxLayout(self.drop_hint)
        hint_layout.setAlignment(Qt.AlignCenter)
        hint_layout.setSpacing(14)
        self.hint_icon = QLabel()
        self.hint_icon.setAlignment(Qt.AlignCenter)
        self.hint_icon.setPixmap(icon_pixmap("arrow-down-to-line", COLOR_MUTED, 44))
        hint_text = QLabel("Drop PDFs, Word, Excel, PowerPoint,\nimages, audio, HTML — or whole folders")
        hint_text.setAlignment(Qt.AlignCenter)
        hint_layout.addWidget(self.hint_icon)
        hint_layout.addWidget(hint_text)
        self.stack.addWidget(self.drop_hint)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("fileScroll")
        self.scroll.setWidgetResizable(True)
        # Never scroll sideways — rows must always fit the window width so the
        # action chips stay visible; long names/sub-lines elide instead.
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        list_container = QWidget()
        list_container.setObjectName("fileListContainer")
        self.list_layout = QVBoxLayout(list_container)
        self.list_layout.setContentsMargins(0, 0, 4, 0)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch()
        self.scroll.setWidget(list_container)
        self.stack.addWidget(self.scroll)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.hide()
        root.addWidget(self.progress)

        bottom = QHBoxLayout()
        self.browse_button = QPushButton("Add Files…")
        self.browse_button.setIcon(themed_icon("plus", "#d6d8e0", 11))
        self.browse_button.clicked.connect(self.browse_files)
        self.clear_button = QPushButton("Clear")
        self.clear_button.setIcon(themed_icon("trash", "#d6d8e0", 11))
        self.clear_button.clicked.connect(self.clear_rows)
        self.remove_selected_button = QPushButton("Remove Selected")
        self.remove_selected_button.setIcon(themed_icon("trash", "#e07a7f", 10))
        self.remove_selected_button.setProperty("class", "rowAction")
        self.remove_selected_button.setStyleSheet("QPushButton { background: #3a2020; color: #e07a7f; border-radius: 8px; } QPushButton:hover { background: #4a2828; }")
        self.remove_selected_button.clicked.connect(self.remove_selected)
        self.remove_selected_button.hide()
        self.reveal_selected_button = QPushButton("Reveal Selected")
        self.reveal_selected_button.setIcon(themed_icon("folder", "#9fe0b8", 10))
        self.reveal_selected_button.setProperty("class", "rowAction")
        self.reveal_selected_button.clicked.connect(self.reveal_selected)
        self.reveal_selected_button.hide()
        self.count_label = QLabel("")
        self.count_label.setObjectName("countLabel")
        self.run_button = QPushButton("Run")
        self.run_button.setIcon(themed_icon("refresh", "white", 11))
        self.run_button.setObjectName("runButton")
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(self.on_run_clicked)
        bottom.addWidget(self.browse_button)
        bottom.addWidget(self.clear_button)
        bottom.addWidget(self.remove_selected_button)
        bottom.addWidget(self.reveal_selected_button)
        bottom.addStretch()
        bottom.addWidget(self.count_label)
        bottom.addWidget(self.run_button)
        root.addLayout(bottom)

        # Toolbar buttons that collapse to icon-only on a narrow window. The
        # Run button is dynamic (Run/Stop) so it's handled in refresh_chrome.
        self._compact = False
        self._run_label = "Run"
        self._labeled_buttons = [
            (self.browse_button, "Add Files…"),
            (self.clear_button, "Clear"),
            (self.remove_selected_button, "Remove Selected"),
            (self.reveal_selected_button, "Reveal Selected"),
        ]
        for btn, label in self._labeled_buttons:
            btn.setToolTip(label)

        self.env_label = QLabel("")
        self.env_label.setObjectName("envLabel")
        root.addWidget(self.env_label)

    RESPONSIVE_BREAKPOINT = 560

    def resizeEvent(self, event):
        # Re-apply responsive chip text + label elision to every row, and
        # collapse the toolbar buttons to icon-only, on any window resize — so
        # nothing overflows when the window is small.
        super().resizeEvent(event)
        compact = self.width() < self.RESPONSIVE_BREAKPOINT
        if compact != self._compact:
            self._compact = compact
            self._apply_button_compact()
        for row in self.rows:
            if row.state == DONE:
                row._update_action_layout()
            row._elide_labels()

    def _apply_button_compact(self):
        for btn, label in self._labeled_buttons:
            btn.setText("" if self._compact else label)
        self.run_button.setText("" if self._compact else self._run_label)

    def open_settings(self):
        controller = getattr(self.window, "controller", None)
        if controller:
            controller.open_settings()

    # ---- environment ----
    def set_markitdown(self, exe: str):
        self.markitdown_exe = exe
        self.env_label.setText(f"using {exe}")
        if self.worker is None:
            self.worker = QueueWorker(exe, parent=self)
            self.worker.job_started.connect(self.on_job_started)
            self.worker.job_done.connect(self.on_job_done)
            self.worker.job_failed.connect(self.on_job_failed)
            self.worker.start()
        else:
            self.worker.markitdown_exe = exe

    def shutdown(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait(2000)

    # ---- file management ----
    def browse_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose files to convert")
        self.add_files([Path(p) for p in paths])

    def add_files(self, paths) -> list:
        existing = {row.source for row in self.rows}
        new_rows = []
        for path in paths:
            if path in existing:
                continue
            existing.add(path)
            row = FileRow(path)
            row.selection_changed.connect(self.on_row_selection_changed)
            self.rows.append(row)
            new_rows.append(row)
            self.list_layout.insertWidget(self.list_layout.count() - 1, row)
        if new_rows and self.auto_convert.isChecked() and self.markitdown_exe:
            self.enqueue_rows(new_rows)
        self.refresh_chrome()
        return new_rows

    def rows_for(self, paths) -> list:
        """Existing rows whose source is in `paths` — lets the dock reflect a
        file that was already added/converted in a previous drop."""
        wanted = set(paths)
        return [row for row in self.rows if row.source in wanted]

    def convert_pending(self, rows):
        """Enqueue any of `rows` that aren't already done/in-flight. Used by the
        dock's Convert button when auto-convert is off."""
        todo = [r for r in rows if r.state in (PENDING, ERROR)]
        if todo and self.markitdown_exe:
            self.enqueue_rows(todo)
            self.refresh_chrome()

    def clear_rows(self):
        if self.in_flight():
            return
        for row in self.rows:
            row.setParent(None)
            row.deleteLater()
        self.rows = []
        self.batch_total = self.batch_done = 0
        self.progress.hide()
        self.refresh_chrome()
        self.cleared.emit()      # mirror the clear into the drop zone

    def remove_selected(self):
        selected = [r for r in self.rows if r.selected and r.state != RUNNING]
        for row in selected:
            self.rows.remove(row)
            row.setParent(None)
            row.deleteLater()
        self.refresh_chrome()

    def reveal_selected(self):
        for row in self.rows:
            if row.selected and row.md_path:
                reveal_in_file_manager(row.md_path)

    def on_row_selection_changed(self, _row):
        self.refresh_chrome()

    def in_flight(self) -> int:
        return self.batch_total - self.batch_done

    def refresh_chrome(self):
        pending = sum(1 for row in self.rows if row.state in (PENDING, ERROR))
        busy = self.in_flight() > 0
        selected = [r for r in self.rows if r.selected]
        self.stack.setCurrentWidget(self.scroll if self.rows else self.drop_hint)
        if not busy:
            self.count_label.setText(f"{len(self.rows)} file(s)" if self.rows else "")
        if busy:
            self._run_label = "Stop"
            self.run_button.setIcon(themed_icon("square", "white", 11))
            self.run_button.setToolTip("Stop after the current file; queued files go back to pending")
            self.run_button.setEnabled(True)
        else:
            self._run_label = "Run"
            self.run_button.setIcon(themed_icon("refresh", "white", 11))
            self.run_button.setToolTip("Run conversion")
            self.run_button.setEnabled(pending > 0 and self.markitdown_exe is not None)
        self.run_button.setText("" if self._compact else self._run_label)
        self.clear_button.setEnabled(bool(self.rows) and not busy)
        removable = [r for r in selected if r.state != RUNNING]
        revealable = [r for r in selected if r.md_path]
        self.remove_selected_button.setVisible(bool(removable))
        self.reveal_selected_button.setVisible(bool(revealable))

    # ---- conversion queue ----
    def on_run_clicked(self):
        if self.in_flight():
            self.stop_queue()
        else:
            self.enqueue_rows([row for row in self.rows if row.state in (PENDING, ERROR)])
        self.refresh_chrome()

    def stop_queue(self):
        drained = self.worker.clear_pending() if self.worker else []
        for row in drained:
            row.set_state(PENDING)
        self.batch_total -= len(drained)
        if self.batch_done >= self.batch_total:
            self.progress.hide()
        else:
            self.progress.setMaximum(max(self.batch_total, 1))
        if drained:
            self.window.toast.show_message(f"Stopped — {len(drained)} file(s) back to pending")

    def enqueue_rows(self, rows):
        if not rows or not self.worker:
            return
        if not self.in_flight():
            self.batch_total = self.batch_done = 0
        for row in rows:
            row.set_state(QUEUED)
            self.batch_total += 1
            self.worker.enqueue(row)
        self.progress.setRange(0, self.batch_total)
        self.progress.setValue(self.batch_done)
        self.progress.show()

    def on_job_started(self, row):
        row.set_state(RUNNING)
        self.count_label.setText(f"Converting {self.batch_done + 1}/{self.batch_total} — {row.source.name}")

    def on_job_done(self, row, output):
        row.set_state(DONE, output)
        self.row_converted.emit(row, output)
        self._job_finished()

    def on_job_failed(self, row, error):
        row.set_state(ERROR, error)
        self.row_failed.emit(row, error)
        self.window.toast.show_message(f"Could not convert {row.source.name}", kind="error")
        self._job_finished()

    def _job_finished(self):
        self.batch_done += 1
        self.progress.setMaximum(self.batch_total)
        self.progress.setValue(self.batch_done)
        if self.batch_done >= self.batch_total:
            ok = sum(1 for row in self.rows if row.state == DONE)
            failed = sum(1 for row in self.rows if row.state == ERROR)
            if failed:
                self.count_label.setText(f"Done — {ok} converted, {failed} failed")
                self.window.toast.show_message(f"{ok} converted, {failed} failed", kind="error")
            else:
                self.count_label.setText(f"Done — {ok} converted")
                self.window.toast.show_message(f"All {ok} file(s) converted", kind="success")
            QTimer.singleShot(2500, self.progress.hide)
        self.refresh_chrome()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(620, 700)
        self.setMinimumSize(480, 460)
        self.setAcceptDrops(True)
        self.settings = QSettings("thekiwidev", "tomd")
        self._restore_geometry()
        self.controller = None       # set by AppController; used by the shortcut

        # ⌘, / Ctrl+, opens Settings from the window view.
        prefs = QShortcut(QKeySequence(QKeySequence.StandardKey.Preferences), self)
        prefs.activated.connect(lambda: self.controller and self.controller.open_settings())

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        wrapper = QVBoxLayout(central)
        wrapper.setContentsMargins(0, 0, 0, 0)

        self.pages = QStackedWidget()
        wrapper.addWidget(self.pages)

        report = backend.environment_report()
        self.main_page = MainPage(self)
        self.setup_page = SetupPage(report)
        self.setup_page.setup_complete.connect(self.on_setup_complete)
        self.pages.addWidget(self.main_page)
        self.pages.addWidget(self.setup_page)

        self.toast = Toast(central)

        if report["markitdown"]:
            self.main_page.set_markitdown(report["markitdown"])
            self.pages.setCurrentWidget(self.main_page)
        else:
            self.pages.setCurrentWidget(self.setup_page)

    def on_setup_complete(self, exe: str):
        self.main_page.set_markitdown(exe)
        self.pages.setCurrentWidget(self.main_page)
        self.toast.show_message("MarkItDown is ready", kind="success")

    def _restore_geometry(self):
        saved = self.settings.value("window_geometry")
        if isinstance(saved, QByteArray) and not saved.isEmpty():
            self.restoreGeometry(saved)
            self._clamp_on_screen()

    def _clamp_on_screen(self):
        """If restored geometry lands off every screen (e.g. an unplugged
        monitor), recenter the window on the primary screen."""
        frame = self.frameGeometry()
        if any(s.availableGeometry().intersects(frame) for s in QGuiApplication.screens()):
            return
        available = QGuiApplication.primaryScreen().availableGeometry()
        self.resize(min(self.width(), available.width()),
                    min(self.height(), available.height()))
        self.move(available.center() - self.rect().center())

    def closeEvent(self, event):
        # Closing the main window just hides it — tomd keeps running in the tray
        # (and the dock stays live). The worker is stopped on app quit instead.
        self.settings.setValue("window_geometry", self.saveGeometry())
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.toast.isVisible():
            self.toast.reposition()

    # ---- drag & drop in (forwarded to the main page) ----
    def dragEnterEvent(self, event):
        if event.source() is not None:
            event.ignore()
            return
        if event.mimeData().hasUrls() and self.pages.currentWidget() is self.main_page:
            self._set_drag_over(True)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._set_drag_over(False)

    def dropEvent(self, event):
        self._set_drag_over(False)
        added = self.main_page.add_files(collect_paths(event.mimeData().urls()))
        if not added:
            self.toast.show_message("Nothing convertible in that drop", kind="error")
        event.acceptProposedAction()

    def _set_drag_over(self, over: bool):
        hint = self.main_page.drop_hint
        hint.setProperty("dragOver", over)
        self.main_page.hint_icon.setPixmap(
            icon_pixmap("arrow-down-to-line", "#b9b0fa" if over else COLOR_MUTED, 44)
        )
        hint.style().unpolish(hint)
        hint.style().polish(hint)


DOCK_STYLE = f"""
QFrame#dockRoot {{
    background: #16171d;
    border: 1px solid #2a2c35;
    border-radius: 14px;
}}
QLabel#dockTitle {{
    color: {COLOR_TEXT};
    font-family: "Space Grotesk", -apple-system, "Segoe UI", sans-serif;
    font-size: 14px; font-weight: 500;
}}
QPushButton#dockIconBtn {{
    background: transparent; border: none; border-radius: 6px;
    color: {COLOR_MUTED}; padding: 2px 8px; font-size: 12px;
}}
QPushButton#dockIconBtn:hover {{ background: #23252e; }}
QFrame#dockDrop {{
    border: 1.5px dashed #34363f; border-radius: 10px;
}}
QFrame#dockDrop[dragOver="true"] {{
    border-color: {COLOR_ACCENT}; background: #1d1b2e;
}}
QLabel#dockHint {{ color: {COLOR_MUTED}; font-size: 12px; padding: 28px 8px; }}
QFrame#dockEntry {{ background: #1e1f26; border-radius: 8px; }}
QLabel#dockEntryName {{
    color: {COLOR_TEXT};
    font-family: "Inter", -apple-system, "Segoe UI", sans-serif; font-size: 12px;
}}
QScrollArea#dockScroll {{ background: transparent; border: none; }}
QPushButton#dockConvert {{
    background: {COLOR_ACCENT}; color: white; border: none; border-radius: 8px;
    padding: 6px 16px; font-size: 12px; font-weight: 600;
}}
QPushButton#dockConvert:hover {{ background: #8576f5; }}
"""

DOCK_MENU_STYLE = (
    "QMenu { background: #1e1f26; border: 1px solid #34363f; border-radius: 8px; padding: 4px; }"
    "QMenu::item { color: #d6d8e0; padding: 7px 16px; font-size: 12px; border-radius: 5px; }"
    "QMenu::item:selected { background: #2a2c35; }"
)

COMBO_STYLE = (
    "QComboBox { background: #1e1f26; color: #d6d8e0; border: 1px solid #34363f;"
    " border-radius: 7px; padding: 5px 10px; font-size: 12px; min-width: 120px; }"
    "QComboBox:hover { border-color: #4a4d59; }"
    "QComboBox::drop-down { border: none; width: 18px; }"
    "QComboBox QAbstractItemView { background: #1e1f26; color: #d6d8e0;"
    " border: 1px solid #34363f; selection-background-color: #2a2c35; outline: none; }"
)

SENSOR_STYLE = f"""
QFrame#sensorNub {{
    background: rgba(22, 23, 29, 0.78);
    border: 1px solid {COLOR_ACCENT};
    border-radius: 14px;
}}
QFrame#sensorNub[dragOver="true"] {{ background: rgba(40, 36, 70, 0.92); }}
QLabel#sensorHint {{ color: {COLOR_MUTED}; font-size: 9px; }}
"""


class DockEntry(QFrame):
    """One compact file line inside the dock: status + elided name + a
    drag-out handle (enabled once the .md exists)."""

    _NAME_MIN_WIDTH = 70

    def __init__(self, source: Path, parent=None):
        super().__init__(parent)
        self.setObjectName("dockEntry")
        self.source = source
        self.row = None              # the shared MainPage FileRow this mirrors
        self._full_name = source.name

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(7)

        self.status_label = QLabel()
        self.status_label.setFixedSize(14, 14)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setPixmap(icon_pixmap("clock", COLOR_MUTED, 11))
        layout.addWidget(self.status_label)

        self.name_label = QLabel(source.name)
        self.name_label.setObjectName("dockEntryName")
        self.name_label.setToolTip(source.name)
        self.name_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.name_label.setMinimumWidth(self._NAME_MIN_WIDTH)
        layout.addWidget(self.name_label, stretch=1)

        # Icon-only action chips — same order as the main window's FileRow
        # (copy, drag, reveal) so the two views feel like one component.
        self.copy_button = ActionChip("copy", "Copy MD")
        self.copy_button.setToolTip("Copy the markdown content to the clipboard")
        self.copy_button.set_text_visible(False)
        self.copy_button.clicked.connect(self._copy_markdown)
        self.copy_button.hide()
        layout.addWidget(self.copy_button)

        self.drag_chip = DragChip()
        self.drag_chip.set_text_visible(False)   # icon-only — the dock is narrow
        self.drag_chip.hide()
        layout.addWidget(self.drag_chip)

        self.reveal_button = ActionChip("folder", "Reveal")
        self.reveal_button.setToolTip("Show the .md file in Finder")
        self.reveal_button.set_text_visible(False)
        self.reveal_button.clicked.connect(self._reveal)
        self.reveal_button.hide()
        layout.addWidget(self.reveal_button)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        fm = self.name_label.fontMetrics()
        self.name_label.setText(
            fm.elidedText(self._full_name, Qt.ElideMiddle, max(self.name_label.width(), 0))
        )

    def _copy_markdown(self):
        if not self.row:
            return
        self.row.copy_markdown()
        self.copy_button.set_content("check", "Copied")
        QTimer.singleShot(1500, lambda: self.copy_button.set_content("copy", "Copy MD"))

    def _reveal(self):
        if self.row:
            self.row.reveal()

    def set_running(self):
        self.status_label.setPixmap(icon_pixmap("loader", COLOR_AMBER, 11))

    def set_done(self, md_path: Path):
        self.status_label.setPixmap(icon_pixmap("check", COLOR_GREEN, 11))
        self.drag_chip.md_path = md_path
        self.drag_chip.show()
        self.copy_button.show()
        self.reveal_button.show()

    def set_failed(self, error: str):
        self.status_label.setPixmap(icon_pixmap("x", COLOR_RED, 11))
        self.setToolTip(error or "Conversion failed")


class DockWindow(QWidget):
    """Always-on-top, frameless mini-window pinned to a screen corner. Files
    dropped here are converted through the shared MainPage queue; finished
    markdown can be dragged straight back out.

    Can appear as a translucent *ghost* (summoned by the edge sensor): a drag
    hovering over it for a moment 'opens' it (solidifies); dragging away
    dismisses it."""

    opened = Signal()       # ghost solidified into the real drop zone
    dismissed = Signal()    # ghost left without opening — re-arm the sensor

    def __init__(self, controller: "MainPage"):
        super().__init__()
        self.controller = controller
        self.settings = QSettings("thekiwidev", "tomd")
        self.anchor = self.settings.value("dock_anchor", "bottom-right")
        if self.anchor not in DOCK_ANCHORS:
            self.anchor = "bottom-right"
        self._entries = {}           # Path -> DockEntry
        self._ghost = False          # showing as a translucent preview
        self._transient = False      # summoned by a drag, not yet dropped/pinned
        self._dwell = QTimer(self, singleShot=True, interval=1000)
        self._dwell.timeout.connect(self._open_from_ghost)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAcceptDrops(True)
        self.setFixedSize(300, 260)   # compact + predictable; entries scroll
        self.setStyleSheet(DOCK_STYLE)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.root = QFrame()
        self.root.setObjectName("dockRoot")
        outer.addWidget(self.root)
        root = QVBoxLayout(self.root)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(10)

        # Header: title + open-app + close(hide)
        header = QHBoxLayout()
        header.setSpacing(6)
        logo = QLabel()
        logo.setPixmap(icon_pixmap("hash", COLOR_ACCENT, 15))
        title = QLabel("tomd")
        title.setObjectName("dockTitle")
        header.addWidget(logo)
        header.addWidget(title)
        header.addStretch()
        self.anchor_button = QPushButton()
        self.anchor_button.setObjectName("dockIconBtn")
        self.anchor_button.setIcon(themed_icon("grip", COLOR_MUTED, 13))
        self.anchor_button.setToolTip("Dock position")
        self.anchor_button.setFixedSize(24, 24)
        self.anchor_button.clicked.connect(self._show_anchor_menu)
        self.open_button = QPushButton()
        self.open_button.setObjectName("dockIconBtn")
        self.open_button.setIcon(themed_icon("arrow-down-to-line", COLOR_MUTED, 13))
        self.open_button.setToolTip("Open the full tomd window")
        self.open_button.setFixedSize(24, 24)
        self.open_button.clicked.connect(self.open_main_window)
        self.close_button = QPushButton()
        self.close_button.setObjectName("dockIconBtn")
        self.close_button.setIcon(themed_icon("x", COLOR_MUTED, 13))
        self.close_button.setToolTip("Hide the dock (tomd keeps running)")
        self.close_button.setFixedSize(24, 24)
        self.close_button.clicked.connect(self.close)   # close() → closeEvent → re-arm sensor
        header.addWidget(self.anchor_button)
        header.addWidget(self.open_button)
        header.addWidget(self.close_button)
        root.addLayout(header)

        # Drop area / entry list
        self.drop_zone = QFrame()
        self.drop_zone.setObjectName("dockDrop")
        dz = QVBoxLayout(self.drop_zone)
        dz.setContentsMargins(0, 0, 0, 0)
        self.empty_hint = QLabel("Drop files here to convert")
        self.empty_hint.setObjectName("dockHint")
        self.empty_hint.setAlignment(Qt.AlignCenter)
        dz.addWidget(self.empty_hint)
        self.scroll = QScrollArea()
        self.scroll.setObjectName("dockScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.NoFrame)
        list_container = QWidget()
        self.list_layout = QVBoxLayout(list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(5)
        self.list_layout.addStretch()
        self.scroll.setWidget(list_container)
        self.scroll.hide()
        dz.addWidget(self.scroll)
        root.addWidget(self.drop_zone, stretch=1)

        # Footer: Convert (when files are pending) + Clear
        footer = QHBoxLayout()
        self.convert_button = QPushButton("Convert")
        self.convert_button.setObjectName("dockConvert")
        self.convert_button.setIcon(themed_icon("refresh", "white", 11))
        self.convert_button.clicked.connect(self._convert_pending)
        self.convert_button.hide()
        self.clear_button = QPushButton("Clear")
        self.clear_button.setObjectName("dockIconBtn")
        # Clear is universal: delegate to the shared controller, which empties
        # the queue and emits `cleared` so both views clear together.
        self.clear_button.clicked.connect(controller.clear_rows)
        self.clear_button.hide()
        footer.addWidget(self.clear_button)
        footer.addStretch()
        footer.addWidget(self.convert_button)
        root.addLayout(footer)

        controller.row_converted.connect(self._on_converted)
        controller.row_failed.connect(self._on_failed)
        controller.cleared.connect(self.clear_entries)

    # ---- positioning ----
    def _target_screen(self):
        return self.screen() or QGuiApplication.primaryScreen()

    def reposition(self):
        geo = dock_geometry(self.anchor, self._target_screen().availableGeometry(), self.size())
        self.setGeometry(geo)

    def showEvent(self, event):
        super().showEvent(event)
        self.reposition()

    def set_anchor(self, anchor: str):
        self.anchor = anchor
        self.settings.setValue("dock_anchor", anchor)
        self.reposition()

    def _show_anchor_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(DOCK_MENU_STYLE)
        for key in DOCK_ANCHORS:
            act = menu.addAction(DOCK_ANCHOR_LABELS[key])
            act.setCheckable(True)
            act.setChecked(key == self.anchor)
            act.triggered.connect(lambda _=False, k=key: self.set_anchor(k))
        menu.exec(self.anchor_button.mapToGlobal(QPoint(0, self.anchor_button.height())))

    def open_main_window(self):
        win = self.controller.window
        win.show()
        win.raise_()
        win.activateWindow()

    # ---- ghost mode (summoned by the edge sensor) ----
    def show_ghost(self):
        """Appear translucently at the anchor; after a short dwell the drag
        opens it. This open is transient — leaving without a drop dismisses it."""
        self._ghost = True
        self._transient = True
        self.setWindowOpacity(0.62)
        self.show()
        self.raise_()
        self._dwell.start()              # ghost shows for ~1s, then solidifies

    def pin(self):
        """Make the drop zone a persistent window (opened from the tray, or
        after a drop) — no longer auto-dismissed by a drag leaving."""
        self._ghost = False
        self._transient = False
        self.setWindowOpacity(1.0)

    def _open_from_ghost(self):
        if self._ghost:
            self._ghost = False
            self.setWindowOpacity(1.0)
            self.opened.emit()

    # ---- drag & drop in ----
    def dragEnterEvent(self, event):
        if event.source() is None and event.mimeData().hasUrls():
            self._set_drag_over(True)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._set_drag_over(False)
        if self._transient:
            # Summoned by a drag but the file was carried away without dropping
            # — dismiss the whole zone and re-arm the hot-corner.
            self._dwell.stop()
            self._ghost = False
            self._transient = False
            self.hide()
            self.dismissed.emit()

    def dropEvent(self, event):
        self._set_drag_over(False)
        self._dwell.stop()
        opened = self._ghost or self._transient
        self.pin()                       # a drop pins the zone open to show results
        if opened:
            self.opened.emit()
        paths = collect_paths(event.mimeData().urls())
        self._accept_drop(paths)
        event.acceptProposedAction()

    def _set_drag_over(self, over: bool):
        self.drop_zone.setProperty("dragOver", over)
        self.drop_zone.style().unpolish(self.drop_zone)
        self.drop_zone.style().polish(self.drop_zone)

    def _accept_drop(self, paths):
        if not paths:
            return
        new_rows = self.controller.add_files(paths)
        # Track both freshly-added rows and any that already existed (e.g. a
        # file dropped earlier on the main window) so the dock reflects them.
        for row in new_rows + self.controller.rows_for(paths):
            self._track(row)
        self._refresh_chrome()

    def _track(self, row):
        if row.source in self._entries:
            return
        entry = DockEntry(row.source)
        entry.row = row
        self._entries[row.source] = entry
        self.list_layout.insertWidget(self.list_layout.count() - 1, entry)
        if row.state == RUNNING:
            entry.set_running()
        elif row.state == DONE and row.md_path:
            entry.set_done(row.md_path)
        elif row.state == ERROR:
            entry.set_failed("Conversion failed")

    def _on_converted(self, row, md_path):
        entry = self._entries.get(row.source)
        if entry:
            entry.set_done(Path(md_path))
            self._refresh_chrome()

    def _on_failed(self, row, error):
        entry = self._entries.get(row.source)
        if entry:
            entry.set_failed(error)
            self._refresh_chrome()

    def _convert_pending(self):
        self.controller.convert_pending([e.row for e in self._entries.values() if e.row])
        for entry in self._entries.values():
            if entry.row and entry.row.state in (QUEUED, RUNNING):
                entry.set_running()
        self._refresh_chrome()

    def clear_entries(self):
        for entry in self._entries.values():
            entry.setParent(None)
        self._entries.clear()
        self._refresh_chrome()

    def _refresh_chrome(self):
        has = bool(self._entries)
        self.empty_hint.setVisible(not has)
        self.scroll.setVisible(has)
        self.clear_button.setVisible(has)
        pending = any(e.row and e.row.state in (PENDING, ERROR) for e in self._entries.values())
        self.convert_button.setVisible(pending and self.controller.markitdown_exe is not None)

    def closeEvent(self, event):
        # The dock never truly closes — hide it; tomd lives in the tray. Emit
        # dismissed so the controller re-arms the hot-corner sensor.
        event.ignore()
        self._ghost = False
        self._transient = False
        self.setWindowOpacity(1.0)
        self.hide()
        self.dismissed.emit()


def checkbox_indicator_rule() -> str:
    """QSS can only load indicator images from files, so write the checkmark
    SVG into the app data dir and point a stylesheet rule at it."""
    path = backend.app_data_dir() / "check-indicator.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        'stroke="white" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M20 6 9 17l-5-5"/></svg>'
    )
    url = path.as_posix()
    return f'QCheckBox::indicator:checked {{ image: url("{url}"); }}'


class EdgeSensor(QWidget):
    """A small, faint hot-corner that sits at the drop-zone anchor. It exists
    only to notice a file being dragged toward the corner: a drag entering it
    fires `approached` (the controller then summons the ghost drop zone), and a
    file dropped straight on it fires `dropped`."""

    approached = Signal()
    dropped = Signal(list)
    SIZE = QSize(116, 116)

    def __init__(self):
        super().__init__()
        self.anchor = "bottom-right"
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # Idle, this window is invisible but still on top of everything — without
        # this it swallows every click in its corner, turning whatever is
        # underneath (another app, or tomd's own window) into dead space.
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAcceptDrops(True)
        self.setFixedSize(self.SIZE)
        self.setStyleSheet(SENSOR_STYLE)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        self.nub = QFrame()
        self.nub.setObjectName("sensorNub")
        nl = QVBoxLayout(self.nub)
        nl.setAlignment(Qt.AlignCenter)
        nl.setSpacing(3)
        icon = QLabel()
        icon.setPixmap(icon_pixmap("hash", COLOR_ACCENT, 18))
        icon.setAlignment(Qt.AlignCenter)
        hint = QLabel("drop here")
        hint.setObjectName("sensorHint")
        hint.setAlignment(Qt.AlignCenter)
        nl.addWidget(icon)
        nl.addWidget(hint)
        outer.addWidget(self.nub)
        # Invisible at idle ("hidden until you drag to it") — the window still
        # catches an approaching drag; the ghost drop zone is the visible cue.
        self.nub.hide()

    def place_at(self, anchor: str, screen: QRect):
        self.anchor = anchor
        self.setGeometry(dock_geometry(anchor, screen, self.SIZE, margin=2))

    def _highlight(self, on: bool):
        self.nub.setProperty("dragOver", on)
        self.nub.style().unpolish(self.nub)
        self.nub.style().polish(self.nub)

    def dragEnterEvent(self, event):
        if event.source() is None and event.mimeData().hasUrls():
            self._highlight(True)
            self.approached.emit()
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._highlight(False)

    def dropEvent(self, event):
        self._highlight(False)
        self.dropped.emit(collect_paths(event.mimeData().urls()))
        event.acceptProposedAction()


class SettingsWindow(QWidget):
    """Standalone preferences window: configure the drop zone, menu-bar mode,
    and start-at-login. Each control applies live through the AppController."""

    def __init__(self, controller: "AppController"):
        super().__init__()
        self.controller = controller
        self.setWindowTitle(f"{APP_NAME} — Settings")
        self.setObjectName("centralWidget")
        self.setMinimumWidth(420)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(16)

        title = QLabel("Settings")
        title.setObjectName("titleLabel")
        root.addWidget(title)

        # Drop zone
        root.addWidget(self._section("Drop zone"))
        self.dropzone_check = QCheckBox("Enable the drop zone")
        self.dropzone_check.setChecked(controller.is_dropzone_enabled())
        self.dropzone_check.toggled.connect(controller.set_dropzone_enabled)
        root.addWidget(self.dropzone_check)

        pos_row = QHBoxLayout()
        pos_label = QLabel("Position")
        pos_label.setObjectName("subtitleLabel")
        self.anchor_combo = QComboBox()
        self.anchor_combo.setStyleSheet(COMBO_STYLE)
        for key in DOCK_ANCHORS:
            self.anchor_combo.addItem(DOCK_ANCHOR_LABELS[key], key)
        idx = self.anchor_combo.findData(controller.current_anchor())
        self.anchor_combo.setCurrentIndex(max(idx, 0))
        self.anchor_combo.currentIndexChanged.connect(
            lambda _: controller.set_anchor(self.anchor_combo.currentData())
        )
        pos_row.addWidget(pos_label)
        pos_row.addStretch()
        pos_row.addWidget(self.anchor_combo)
        root.addLayout(pos_row)

        self.auto_check = QCheckBox("Auto-convert files on drop")
        self.auto_check.setChecked(controller.is_auto_convert())
        self.auto_check.toggled.connect(controller.set_auto_convert)
        controller.window.main_page.auto_convert.toggled.connect(self.auto_check.setChecked)
        root.addWidget(self.auto_check)

        # App behaviour
        root.addWidget(self._section("App"))
        self.menubar_check = QCheckBox("Run in the menu bar only (hide Dock icon)")
        self.menubar_check.setChecked(controller.is_menu_bar_only())
        self.menubar_check.toggled.connect(controller.set_menu_bar_only)
        root.addWidget(self.menubar_check)

        self.login_check = QCheckBox("Start tomd when I turn on my computer")
        self.login_check.setChecked(controller.is_start_at_login())
        self.login_check.toggled.connect(controller.set_start_at_login)
        root.addWidget(self.login_check)

        root.addStretch()
        hint = QLabel("Changes apply immediately.")
        hint.setObjectName("envLabel")
        root.addWidget(hint)

    def _section(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f'color: {COLOR_MUTED}; font-size: 11px; font-weight: 600; '
            'letter-spacing: 0.08em; text-transform: uppercase; margin-top: 4px;'
        )
        return lbl


class AppController:
    """Owns the windows, tray, and drop zone, and applies persisted settings.
    The single place that knows how the pieces fit together."""

    def __init__(self, app):
        self.app = app
        self.settings = QSettings("thekiwidev", "tomd")
        self.window = MainWindow()
        self.window.controller = self        # lets the window/shortcut open Settings
        self.dock = DockWindow(self.window.main_page)
        self.settings_window = None

        # Hidden hot-corner that summons the ghost drop zone on drag-approach.
        self.sensor = EdgeSensor()
        self.sensor.approached.connect(self._on_sensor_approach)
        self.sensor.dropped.connect(self._on_sensor_drop)
        self.dock.opened.connect(self._on_dock_opened)
        self.dock.dismissed.connect(self._rearm_sensor)
        # If the ghost is summoned but the drag never lands on it, give up.
        self._orphan = QTimer(self.window, singleShot=True, interval=2000)
        self._orphan.timeout.connect(self._on_orphan_timeout)

        self.tray = self._build_tray()
        app.aboutToQuit.connect(self.window.main_page.shutdown)
        self._apply_startup()

    # ---- persisted getters ----
    def is_dropzone_enabled(self) -> bool:
        return self.settings.value("dropzone_enabled", True, type=bool)

    def current_anchor(self) -> str:
        a = self.settings.value("dock_anchor", "bottom-right")
        return a if a in DOCK_ANCHORS else "bottom-right"

    def is_auto_convert(self) -> bool:
        return self.window.main_page.auto_convert.isChecked()

    def is_menu_bar_only(self) -> bool:
        return self.settings.value("menu_bar_only", False, type=bool)

    def is_start_at_login(self) -> bool:
        return native.is_login_item_enabled()

    # ---- setters (apply live) ----
    def set_dropzone_enabled(self, enabled: bool):
        self.settings.setValue("dropzone_enabled", enabled)
        if enabled:
            self._arm_sensor()
        else:
            self.sensor.hide()
            self.dock.hide()

    def set_anchor(self, anchor: str):
        self.dock.set_anchor(anchor)
        if self.sensor.isVisible():
            self._arm_sensor()   # move the hot-corner to the new anchor too

    def set_auto_convert(self, enabled: bool):
        self.window.main_page.auto_convert.setChecked(enabled)

    def set_menu_bar_only(self, enabled: bool):
        self.settings.setValue("menu_bar_only", enabled)
        native.set_dock_icon_visible(not enabled)

    def set_start_at_login(self, enabled: bool):
        native.set_login_item(enabled)

    # ---- actions ----
    def show_main_window(self):
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def show_drop_zone(self):
        if not self.is_dropzone_enabled():
            self.settings.setValue("dropzone_enabled", True)
            if self.settings_window:
                self.settings_window.dropzone_check.setChecked(True)
        self._orphan.stop()
        self.sensor.hide()
        self.dock.pin()              # opened deliberately — persistent, not transient
        self.dock.show()
        self.dock.raise_()
        self._pin_all_spaces(self.dock)

    def _pin_all_spaces(self, win):
        # Only touch native NSWindow APIs on the real macOS GUI platform; on the
        # offscreen/test platform winId() isn't a valid NSView and would crash.
        if QGuiApplication.platformName() == "cocoa":
            native.show_on_all_spaces(win)

    # ---- ghost drop zone (edge sensor → ghost → open) ----
    def _arm_sensor(self):
        if not self.is_dropzone_enabled():
            return
        screen = (self.window.screen() or QGuiApplication.primaryScreen())
        self.sensor.place_at(self.current_anchor(), screen.availableGeometry())
        self.sensor.show()
        self.sensor.raise_()
        self._pin_all_spaces(self.sensor)

    def _rearm_sensor(self):
        self.dock.hide()
        self._orphan.stop()
        self._arm_sensor()

    def _on_sensor_approach(self):
        # A drag reached the hot-corner: summon the ghost drop zone there.
        self.sensor.hide()
        self.dock.set_anchor(self.current_anchor())
        self.dock.show_ghost()
        self._pin_all_spaces(self.dock)
        self._orphan.start()

    def _on_sensor_drop(self, paths):
        # Dropped straight on the hot-corner — open and convert immediately.
        self.show_drop_zone()
        if paths:
            self.dock._accept_drop(paths)

    def _on_dock_opened(self):
        self._orphan.stop()

    def _on_orphan_timeout(self):
        # Ghost was summoned but the drag never engaged it — fade out, re-arm.
        if self.dock._ghost:
            self.dock._ghost = False
            self.dock._transient = False
            self._rearm_sensor()

    def open_settings(self):
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    # ---- startup ----
    def _apply_startup(self):
        native.set_dock_icon_visible(not self.is_menu_bar_only())
        if not self.is_menu_bar_only():
            self.window.show()
        # The drop zone stays hidden; the hot-corner watches for an approaching
        # drag and summons the ghost on demand.
        if self.is_dropzone_enabled():
            self._arm_sensor()

    def _build_tray(self):
        # White app-logo glyph (the # + return arrow) to match the desktop icon.
        tray = QSystemTrayIcon(app_logo_icon("white", 22), parent=self.window)
        tray.setToolTip(APP_NAME)
        menu = QMenu()
        menu.setStyleSheet(DOCK_MENU_STYLE)

        window_act = QAction("Open window view", menu)
        window_act.triggered.connect(self.show_main_window)
        zone_act = QAction("Open drop zone", menu)
        zone_act.triggered.connect(self.show_drop_zone)
        settings_act = QAction("Settings…", menu)
        settings_act.triggered.connect(self.open_settings)

        auto_act = QAction("Auto-convert on drop", menu)
        auto_act.setCheckable(True)
        auto_act.setChecked(self.is_auto_convert())
        auto_act.toggled.connect(self.set_auto_convert)
        self.window.main_page.auto_convert.toggled.connect(auto_act.setChecked)

        quit_act = QAction("Quit tomd", menu)
        quit_act.triggered.connect(self.app.quit)

        menu.addAction(window_act)
        menu.addAction(zone_act)
        menu.addSeparator()
        menu.addAction(settings_act)
        menu.addAction(auto_act)
        menu.addSeparator()
        menu.addAction(quit_act)
        tray.setContextMenu(menu)
        # Clicking the menu-bar icon just shows the menu (handled by Qt) — it
        # must NOT auto-open the window view.
        tray.show()
        return tray


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(STYLE + checkbox_indicator_rule())
    # The app outlives its windows: closing the main window or hiding the drop
    # zone leaves tomd running in the menu bar / tray.
    app.setQuitOnLastWindowClosed(False)

    controller = AppController(app)
    app._controller = controller  # keep a strong reference

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
