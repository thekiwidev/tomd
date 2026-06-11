"""tomd — drag & drop anything, get Markdown.

A tiny GUI wrapper around Microsoft's MarkItDown. Drop files or folders,
hit Run, and a .md file appears next to each source file. Each converted
row lets you copy the markdown, drag the .md file out, or reveal it in
Finder / Explorer.
"""

import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QMimeData, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QDrag, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

APP_NAME = "tomd"

# Extensions MarkItDown can handle. Used to filter folder drops; a file
# dropped directly is always accepted so MarkItDown can have a go at it.
SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".csv",
    ".json", ".xml", ".html", ".htm", ".txt", ".rtf", ".epub", ".msg",
    ".eml", ".wav", ".mp3", ".m4a", ".jpg", ".jpeg", ".png", ".webp",
    ".ipynb", ".zip",
}

PENDING, RUNNING, DONE, ERROR = range(4)

STYLE = """
* { font-family: -apple-system, "SF Pro Text", "Segoe UI", sans-serif; }
QMainWindow, #centralWidget { background: #15161a; }
#titleLabel { color: #f2f3f7; font-size: 22px; font-weight: 700; }
#subtitleLabel { color: #8b8e98; font-size: 13px; }
#dropHint {
    color: #8b8e98; font-size: 15px;
    border: 2px dashed #34363f; border-radius: 14px;
    background: #1a1b20;
}
#dropHint[dragOver="true"] { border-color: #7c6cf0; color: #b9b0fa; background: #1e1d2b; }
#fileScroll { border: none; background: transparent; }
#fileListContainer { background: transparent; }
#fileRow { background: #1e1f26; border-radius: 10px; }
#fileRow[state="done"] { background: #1c2420; }
#fileRow[state="error"] { background: #261d1e; }
#fileName { color: #e8e9ee; font-size: 13px; font-weight: 600; }
#fileSub { color: #7f828d; font-size: 11px; }
#fileSub[state="error"] { color: #e07a7f; }
#statusDot { font-size: 14px; }
QPushButton {
    background: #2a2c35; color: #d6d8e0; border: none;
    border-radius: 8px; padding: 6px 14px; font-size: 12px; font-weight: 600;
}
QPushButton:hover { background: #343742; }
QPushButton:pressed { background: #3d404d; }
QPushButton:disabled { background: #22232a; color: #565963; }
QPushButton#runButton {
    background: #6c5ce7; color: white; font-size: 13px; padding: 9px 22px;
}
QPushButton#runButton:hover { background: #7d6ef0; }
QPushButton#runButton:disabled { background: #3a3554; color: #837fa6; }
QPushButton.rowAction { padding: 4px 10px; font-size: 11px; background: #2a3d33; color: #9fe0b8; }
QPushButton.rowAction:hover { background: #345043; }
#dragChip {
    color: #9fe0b8; background: #2a3d33; border-radius: 8px;
    padding: 4px 10px; font-size: 11px; font-weight: 600;
}
#countLabel { color: #8b8e98; font-size: 12px; }
QScrollBar:vertical { background: transparent; width: 8px; }
QScrollBar::handle:vertical { background: #34363f; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
"""


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


class ConvertWorker(QThread):
    """Runs MarkItDown over the queued files off the UI thread."""

    file_started = Signal(int)
    file_done = Signal(int, str)
    file_failed = Signal(int, str)
    all_finished = Signal(int, int)

    def __init__(self, jobs, parent=None):
        super().__init__(parent)
        self.jobs = jobs  # list of (row_index, source_path)

    def run(self):
        from markitdown import MarkItDown

        converter = MarkItDown()
        ok = failed = 0
        for index, source in self.jobs:
            self.file_started.emit(index)
            try:
                result = converter.convert(str(source))
                output = source.with_suffix(".md")
                output.write_text(result.text_content, encoding="utf-8")
                ok += 1
                self.file_done.emit(index, str(output))
            except Exception as exc:  # noqa: BLE001 — surface every failure per-row
                failed += 1
                self.file_failed.emit(index, str(exc))
        self.all_finished.emit(ok, failed)


class DragChip(QLabel):
    """Small handle that lets the user drag the converted .md out of the app."""

    def __init__(self, parent=None):
        super().__init__("⠿ drag .md", parent)
        self.setObjectName("dragChip")
        self.md_path = None
        self.setCursor(Qt.OpenHandCursor)
        self.setToolTip("Drag this into Finder, an editor, or anywhere that accepts files")

    def mousePressEvent(self, event):
        self._press_pos = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if self.md_path is None:
            return
        if (event.position().toPoint() - self._press_pos).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(str(self.md_path))])
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)


class FileRow(QFrame):
    STATUS_ICONS = {PENDING: "○", RUNNING: "◐", DONE: "✓", ERROR: "✕"}
    STATUS_COLORS = {PENDING: "#8b8e98", RUNNING: "#e6c468", DONE: "#7ddc9a", ERROR: "#e07a7f"}

    def __init__(self, source: Path, parent=None):
        super().__init__(parent)
        self.setObjectName("fileRow")
        self.source = source
        self.md_path = None
        self.state = PENDING

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(10)

        self.status_label = QLabel(self.STATUS_ICONS[PENDING])
        self.status_label.setObjectName("statusDot")
        self.status_label.setFixedWidth(18)
        layout.addWidget(self.status_label)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        self.name_label = QLabel(source.name)
        self.name_label.setObjectName("fileName")
        self.sub_label = QLabel(str(source.parent))
        self.sub_label.setObjectName("fileSub")
        for label in (self.name_label, self.sub_label):
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        text_col.addWidget(self.name_label)
        text_col.addWidget(self.sub_label)
        layout.addLayout(text_col, stretch=1)

        self.copy_button = QPushButton("Copy MD")
        self.copy_button.setProperty("class", "rowAction")
        self.copy_button.setToolTip("Copy the markdown content to the clipboard")
        self.copy_button.clicked.connect(self.copy_markdown)

        self.drag_chip = DragChip()

        self.reveal_button = QPushButton("Reveal")
        self.reveal_button.setProperty("class", "rowAction")
        self.reveal_button.setToolTip("Show the .md file in Finder")
        self.reveal_button.clicked.connect(self.reveal)

        for widget in (self.copy_button, self.drag_chip, self.reveal_button):
            layout.addWidget(widget)
            widget.hide()

    def set_state(self, state, detail=None):
        self.state = state
        self.status_label.setText(self.STATUS_ICONS[state])
        self.status_label.setStyleSheet(f"color: {self.STATUS_COLORS[state]};")
        self.setProperty("state", {DONE: "done", ERROR: "error"}.get(state, ""))
        self.sub_label.setProperty("state", "error" if state == ERROR else "")
        if state == RUNNING:
            self.sub_label.setText("Converting…")
        elif state == DONE:
            self.md_path = Path(detail)
            self.drag_chip.md_path = self.md_path
            self.sub_label.setText(f"→ {self.md_path.name}")
            for widget in (self.copy_button, self.drag_chip, self.reveal_button):
                widget.show()
        elif state == ERROR:
            self.sub_label.setText(detail or "Conversion failed")
            self.sub_label.setToolTip(detail or "")
        for widget in (self, self.sub_label):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def copy_markdown(self):
        if self.md_path and self.md_path.exists():
            QGuiApplication.clipboard().setText(self.md_path.read_text(encoding="utf-8"))
            self.copy_button.setText("Copied ✓")
            QTimer.singleShot(1500, lambda: self.copy_button.setText("Copy MD"))

    def reveal(self):
        if self.md_path:
            reveal_in_file_manager(self.md_path)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(620, 680)
        self.setMinimumSize(480, 420)
        self.setAcceptDrops(True)
        self.rows = []
        self.worker = None

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(12)

        title = QLabel("tomd")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Drop files or folders anywhere in this window, then hit Run.")
        subtitle.setObjectName("subtitleLabel")
        root.addWidget(title)
        root.addWidget(subtitle)

        # Stacked area: big drop hint when empty, file list once populated.
        self.stack = QStackedLayout()
        root.addLayout(self.stack, stretch=1)

        self.drop_hint = QLabel("⬇\n\nDrop PDFs, Word, Excel, PowerPoint,\nimages, audio, HTML — or whole folders")
        self.drop_hint.setObjectName("dropHint")
        self.drop_hint.setAlignment(Qt.AlignCenter)
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

        bottom = QHBoxLayout()
        self.browse_button = QPushButton("Add Files…")
        self.browse_button.clicked.connect(self.browse_files)
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_rows)
        self.count_label = QLabel("")
        self.count_label.setObjectName("countLabel")
        self.run_button = QPushButton("Run ⚡")
        self.run_button.setObjectName("runButton")
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(self.start_conversion)
        bottom.addWidget(self.browse_button)
        bottom.addWidget(self.clear_button)
        bottom.addStretch()
        bottom.addWidget(self.count_label)
        bottom.addWidget(self.run_button)
        root.addLayout(bottom)

    # ---- drag & drop in ----
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.drop_hint.setProperty("dragOver", True)
            self._repolish(self.drop_hint)
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.drop_hint.setProperty("dragOver", False)
        self._repolish(self.drop_hint)

    def dropEvent(self, event):
        self.drop_hint.setProperty("dragOver", False)
        self._repolish(self.drop_hint)
        self.add_files(collect_paths(event.mimeData().urls()))
        event.acceptProposedAction()

    @staticmethod
    def _repolish(widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    # ---- file management ----
    def browse_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose files to convert")
        self.add_files([Path(p) for p in paths])

    def add_files(self, paths):
        existing = {row.source for row in self.rows}
        for path in paths:
            if path in existing:
                continue
            existing.add(path)
            row = FileRow(path)
            self.rows.append(row)
            self.list_layout.insertWidget(self.list_layout.count() - 1, row)
        self.refresh_chrome()

    def clear_rows(self):
        if self.worker and self.worker.isRunning():
            return
        for row in self.rows:
            row.setParent(None)
            row.deleteLater()
        self.rows = []
        self.refresh_chrome()

    def refresh_chrome(self):
        pending = sum(1 for row in self.rows if row.state == PENDING)
        self.stack.setCurrentWidget(self.scroll if self.rows else self.drop_hint)
        self.count_label.setText(f"{len(self.rows)} file(s)" if self.rows else "")
        busy = bool(self.worker and self.worker.isRunning())
        self.run_button.setEnabled(pending > 0 and not busy)
        self.clear_button.setEnabled(bool(self.rows) and not busy)
        self.browse_button.setEnabled(not busy)

    # ---- conversion ----
    def start_conversion(self):
        jobs = [(i, row.source) for i, row in enumerate(self.rows) if row.state in (PENDING, ERROR)]
        if not jobs:
            return
        self.worker = ConvertWorker(jobs, parent=self)
        self.worker.file_started.connect(lambda i: self.rows[i].set_state(RUNNING))
        self.worker.file_done.connect(lambda i, out: (self.rows[i].set_state(DONE, out), self.refresh_chrome()))
        self.worker.file_failed.connect(lambda i, err: (self.rows[i].set_state(ERROR, err), self.refresh_chrome()))
        self.worker.all_finished.connect(self.on_all_finished)
        self.worker.start()
        self.refresh_chrome()

    def on_all_finished(self, ok, failed):
        summary = f"Done — {ok} converted"
        if failed:
            summary += f", {failed} failed"
        self.count_label.setText(summary)
        self.run_button.setEnabled(False)
        self.clear_button.setEnabled(True)
        self.browse_button.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
