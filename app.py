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

from PySide6.QtCore import QByteArray, QMimeData, QSettings, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QDrag, QGuiApplication, QIcon, QPainter, QPixmap, QTransform
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStackedLayout,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

import backend

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
#titleLabel {{ font-family: "Space Grotesk", "Inter", -apple-system, sans-serif; color: #f2f3f7; font-size: 22px; font-weight: 700; }}
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
    border-radius: 8px; padding: 6px 14px; font-size: 12px; font-weight: 600;
}}
QPushButton:hover {{ background: #343742; }}
QPushButton:pressed {{ background: #3d404d; }}
QPushButton:disabled {{ background: #22232a; color: #565963; }}
QPushButton#runButton, QPushButton#installButton {{
    background: #6c5ce7; color: white; font-size: 13px; padding: 9px 22px;
}}
QPushButton#runButton:hover, QPushButton#installButton:hover {{ background: {COLOR_ACCENT}; }}
QPushButton#runButton:disabled, QPushButton#installButton:disabled {{ background: #3a3554; color: #837fa6; }}
QPushButton.rowAction {{ padding: 3px 9px; font-family: "JetBrains Mono", ui-monospace, Menlo, Consolas, monospace; font-size: 11px; background: #2a3d33; color: #9fe0b8; border-radius: 8px; }}
QPushButton.rowAction:hover {{ background: #345043; }}
#dragChip {{
    font-family: "JetBrains Mono", ui-monospace, Menlo, Consolas, monospace;
    color: #9fe0b8; background: #2a3d33; border-radius: 8px;
    padding: 3px 9px; font-size: 11px; font-weight: 600;
}}
#countLabel, #envLabel {{ font-family: "JetBrains Mono", ui-monospace, Menlo, Consolas, monospace; color: {COLOR_MUTED}; font-size: 12px; }}
#envLabel {{ font-size: 10px; }}
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


class DragChip(QWidget):
    """Small handle that lets the user drag the converted .md out of the app."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dragChip")
        self.setAttribute(Qt.WA_StyledBackground, True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(7, 3, 9, 3)
        layout.setSpacing(4)
        grip = QLabel()
        grip.setPixmap(icon_pixmap("grip", "#9fe0b8", 12))
        grip.setFixedSize(14, 14)
        grip.setAlignment(Qt.AlignCenter)
        grip.setAttribute(Qt.WA_TransparentForMouseEvents)
        text = QLabel("drag .md")
        text.setStyleSheet("color: #9fe0b8; font-size: 11px; font-weight: 600; background: transparent;")
        text.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(grip)
        layout.addWidget(text)
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
        text_col.setSpacing(1)
        self.name_label = QLabel(source.name)
        self.name_label.setObjectName("fileName")
        self.name_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

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
        self.sub_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.sub_label.hide()
        sub_row.addWidget(self._sub_icon)
        sub_row.addWidget(self.sub_label)
        sub_row.addStretch()

        text_col.addWidget(self.name_label)
        text_col.addLayout(sub_row)
        layout.addLayout(text_col, stretch=1)

        self.copy_button = QPushButton("Copy MD")
        self.copy_button.setIcon(themed_icon("copy", "#9fe0b8", 9))
        self.copy_button.setProperty("class", "rowAction")
        self.copy_button.setToolTip("Copy the markdown content to the clipboard")
        self.copy_button.clicked.connect(self.copy_markdown)

        self.drag_chip = DragChip()

        self.reveal_button = QPushButton("Reveal")
        self.reveal_button.setIcon(themed_icon("folder", "#9fe0b8", 9))
        self.reveal_button.setProperty("class", "rowAction")
        self.reveal_button.setToolTip("Show the .md file in Finder")
        self.reveal_button.clicked.connect(self.reveal)

        for widget in (self.copy_button, self.drag_chip, self.reveal_button):
            layout.addWidget(widget)
            widget.hide()

    def set_selected(self, value: bool):
        self.selected = value
        self.select_box.set_checked(value)
        self.setProperty("selected", "true" if value else "false")
        self.style().unpolish(self)
        self.style().polish(self)
        self.selection_changed.emit(self)

    def _spin(self):
        self._spin_angle = (self._spin_angle + 30) % 360
        rotated = self._loader_pixmap.transformed(QTransform().rotate(self._spin_angle), Qt.SmoothTransformation)
        self.status_label.setPixmap(rotated)

    def _show_sub_text(self, text: str):
        self._sub_icon.hide()
        self.sub_label.setText(text)
        self.sub_label.show()

    def _show_sub_icon(self):
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
            for widget in (self.copy_button, self.drag_chip, self.reveal_button):
                widget.show()
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
            self.copy_button.setText("Copied")
            self.copy_button.setIcon(themed_icon("check", "#9fe0b8", 9))
            QTimer.singleShot(1500, self._reset_copy_button)

    def _reset_copy_button(self):
        self.copy_button.setText("Copy MD")
        self.copy_button.setIcon(themed_icon("copy", "#9fe0b8", 9))

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
        self.install_button.clicked.connect(self.start_install)
        button_row.addWidget(self.recheck_button)
        button_row.addStretch()
        button_row.addWidget(self.install_button)
        layout.addLayout(button_row)

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
        # uv can bootstrap its own Python, so either one unblocks the install.
        self.install_button.setEnabled(bool(report["python"] or report["uv"]) and not report["markitdown"])

    def recheck(self):
        report = backend.environment_report()
        self.update_checks(report)
        if report["markitdown"]:
            self.setup_complete.emit(report["markitdown"])

    def start_install(self):
        self.install_button.setEnabled(False)
        self.recheck_button.setEnabled(False)
        self.log_view.clear()
        self.worker = SetupWorker(self)
        self.worker.log_line.connect(self.append_log)
        self.worker.finished_setup.connect(self.on_finished)
        self.worker.start()

    def append_log(self, line: str):
        self.log_view.appendPlainText(line)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

    def on_finished(self, ok: bool, error: str):
        self.recheck_button.setEnabled(True)
        if ok:
            self.append_log("✓ Setup complete.")
            self.setup_complete.emit(str(backend.venv_executable("markitdown")))
        else:
            self.append_log(f"Setup failed: {error}")
            self.install_button.setEnabled(True)


class MainPage(QWidget):
    """The converter UI: drop zone, queue, progress, actions."""

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
        self.auto_convert = QCheckBox("Auto-convert on drop")
        self.auto_convert.setChecked(self.settings.value("auto_convert_on_drop", False, type=bool))
        self.auto_convert.toggled.connect(lambda v: self.settings.setValue("auto_convert_on_drop", v))
        header.addWidget(self.auto_convert, alignment=Qt.AlignTop)
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

        self.env_label = QLabel("")
        self.env_label.setObjectName("envLabel")
        root.addWidget(self.env_label)

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

    def add_files(self, paths) -> int:
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
        return len(new_rows)

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
            self.run_button.setText("Stop")
            self.run_button.setIcon(themed_icon("square", "white", 11))
            self.run_button.setToolTip("Stop after the current file; queued files go back to pending")
            self.run_button.setEnabled(True)
        else:
            self.run_button.setText("Run")
            self.run_button.setIcon(themed_icon("refresh", "white", 11))
            self.run_button.setToolTip("")
            self.run_button.setEnabled(pending > 0 and self.markitdown_exe is not None)
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
        self._job_finished()

    def on_job_failed(self, row, error):
        row.set_state(ERROR, error)
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

    def closeEvent(self, event):
        self.main_page.shutdown()
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


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(STYLE + checkbox_indicator_rule())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
