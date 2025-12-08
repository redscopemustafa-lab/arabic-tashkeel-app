"""
Arabic Diacritization (Tashkeel) Desktop App using PySide6.

This single-file application provides a clean GUI that accepts Arabic text,
automatically adds diacritics (harakat), and displays the output in RTL format.
It attempts to use an open-source diacritizer if installed (camel-tools).
If the model is unavailable, it falls back to a lightweight heuristic diacritizer
and documents how to swap in a real model.
"""
from __future__ import annotations

import importlib
import sys
import traceback
from dataclasses import dataclass
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

# Optional dependency detection without try/except around the import.
camel_tools_available = importlib.util.find_spec("camel_tools") is not None
if camel_tools_available:
    from camel_tools.diacritization.pretrained import PretrainedDiacritizer
else:
    PretrainedDiacritizer = None  # type: ignore


ARABIC_DIACRITICS = "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0670"
ARABIC_LETTER_RANGE = (0x0621, 0x064A)


def has_diacritic(char: str) -> bool:
    """Return True if the character is an Arabic diacritic mark."""
    return char in ARABIC_DIACRITICS


@dataclass
class DiacritizationResult:
    text: str
    used_real_model: bool
    model_name: str


class HeuristicDiacritizer:
    """A tiny fallback diacritizer for environments without a ML model.

    This is intentionally simple: it preserves non-Arabic characters and adds a
    fatha (\u064e) on the last letter of each detected Arabic word if that letter
    is undiacritized. The logic is deterministic and fast, making it suitable for
    large texts while providing visible feedback that diacritization occurred.

    The class is separated so users can swap in a real diacritizer by replacing
    the `diacritize` method with any function that accepts and returns a string.
    """

    def diacritize(self, text: str) -> str:
        output = []
        for token in text.split(" "):
            output.append(self._diacritize_token(token))
        return " ".join(output)

    def _diacritize_token(self, token: str) -> str:
        if not token:
            return token
        chars = list(token)
        for idx in range(len(chars) - 1, -1, -1):
            code = ord(chars[idx])
            if ARABIC_LETTER_RANGE[0] <= code <= ARABIC_LETTER_RANGE[1]:
                # Skip if diacritized already.
                if idx + 1 < len(chars) and has_diacritic(chars[idx + 1]):
                    return token
                chars.insert(idx + 1, "\u064e")  # Arabic fatha
                return "".join(chars)
        return token


class CamelToolsDiacritizer:
    """Wrapper around camel_tools' pretrained diacritizer when available."""

    def __init__(self) -> None:
        self.model: Optional[PretrainedDiacritizer] = None
        if PretrainedDiacritizer:
            self.model = PretrainedDiacritizer.pretrained()

    def diacritize(self, text: str) -> str:
        if not self.model:
            raise RuntimeError("camel_tools diacritizer is not initialized.")
        return self.model.diacritize(text)


class DiacritizerEngine:
    """Coordinator that prefers the real model and falls back gracefully."""

    def __init__(self) -> None:
        self._camel_diacritizer: Optional[CamelToolsDiacritizer] = None
        self._fallback = HeuristicDiacritizer()

    def diacritize(self, text: str) -> DiacritizationResult:
        if not text.strip():
            return DiacritizationResult(text="", used_real_model=False, model_name="None")

        if camel_tools_available and self._camel_diacritizer is None:
            self._camel_diacritizer = CamelToolsDiacritizer()

        if self._camel_diacritizer and self._camel_diacritizer.model is not None:
            try:
                return DiacritizationResult(
                    text=self._camel_diacritizer.diacritize(text),
                    used_real_model=True,
                    model_name="camel_tools PretrainedDiacritizer",
                )
            except Exception:
                traceback.print_exc()

        return DiacritizationResult(
            text=self._fallback.diacritize(text),
            used_real_model=False,
            model_name="Heuristic fallback (replace with your model)",
        )


class DiacritizationWorker(QtCore.QObject):
    finished = QtCore.Signal(DiacritizationResult)
    failed = QtCore.Signal(str)
    progress = QtCore.Signal(str)

    def __init__(self, engine: DiacritizerEngine) -> None:
        super().__init__()
        self.engine = engine

    @QtCore.Slot(str)
    def run(self, text: str) -> None:
        try:
            self.progress.emit("⏳ Diacritizing…")
            result = self.engine.diacritize(text)
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class TashkeelWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Arabic Tashkeel - Automatic Diacritization")
        self.resize(1000, 720)
        self.engine = DiacritizerEngine()
        self._setup_ui()
        self._setup_worker()

    def _setup_ui(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background-color: #0f172a; }
            QLabel { color: #e2e8f0; font-size: 14px; }
            QPlainTextEdit { background: #0b1220; color: #e2e8f0; border: 1px solid #1f2937; border-radius: 8px; padding: 8px; font-size: 16px; }
            QPushButton { background-color: #2563eb; color: white; padding: 10px 16px; border: none; border-radius: 8px; font-weight: 600; }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton:disabled { background-color: #475569; color: #cbd5e1; }
            QStatusBar { color: #cbd5e1; }
            """
        )

        central = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        header = QtWidgets.QLabel("أدخِل النص العربي ثم اضغط على زر التشكيل.")
        header.setAlignment(QtCore.Qt.AlignRight)
        header.setLayoutDirection(QtCore.Qt.RightToLeft)
        header.setWordWrap(True)
        layout.addWidget(header)

        editors_layout = QtWidgets.QGridLayout()
        editors_layout.setSpacing(10)

        self.input_edit = QtWidgets.QPlainTextEdit()
        self.input_edit.setPlaceholderText("الصق النص العربي هنا…")
        self.input_edit.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.input_edit.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)

        self.output_edit = QtWidgets.QPlainTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.output_edit.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)

        editors_layout.addWidget(QtWidgets.QLabel("النص الأصلي"), 0, 0)
        editors_layout.addWidget(QtWidgets.QLabel("النص المشكّل"), 0, 1)
        editors_layout.addWidget(self.input_edit, 1, 0)
        editors_layout.addWidget(self.output_edit, 1, 1)
        layout.addLayout(editors_layout)

        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addStretch(1)

        self.status_label = QtWidgets.QLabel("جاهز")
        buttons_layout.addWidget(self.status_label)
        buttons_layout.addStretch(1)

        self.clear_button = QtWidgets.QPushButton("مسح")
        self.clear_button.clicked.connect(self._clear_fields)
        buttons_layout.addWidget(self.clear_button)

        self.copy_button = QtWidgets.QPushButton("نسخ النص المشكّل")
        self.copy_button.clicked.connect(self._copy_output)
        buttons_layout.addWidget(self.copy_button)

        self.diacritize_button = QtWidgets.QPushButton("تشكيــل")
        self.diacritize_button.clicked.connect(self._start_diacritization)
        buttons_layout.addWidget(self.diacritize_button)

        layout.addLayout(buttons_layout)

        footer = QtWidgets.QLabel(
            "يستخدم التطبيق نموذج camel-tools عند توفره، أو خوارزمية مبسطة عند عدم توفر النموذج."
        )
        footer.setAlignment(QtCore.Qt.AlignRight)
        footer.setLayoutDirection(QtCore.Qt.RightToLeft)
        footer.setWordWrap(True)
        layout.addWidget(footer)

        self.setCentralWidget(central)
        self.statusBar().showMessage("Ready")

    def _setup_worker(self) -> None:
        self.thread = QtCore.QThread(self)
        self.worker = DiacritizationWorker(self.engine)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(lambda: None)
        self.worker.finished.connect(self._handle_finished)
        self.worker.failed.connect(self._handle_failed)
        self.worker.progress.connect(self._handle_progress)
        self.thread.start()

    def _start_diacritization(self) -> None:
        text = self.input_edit.toPlainText()
        if not text.strip():
            self._handle_progress("⚠️ الرجاء إدخال نص أولاً")
            return

        self.diacritize_button.setDisabled(True)
        self.status_label.setText("⏳ قيد المعالجة…")
        QtCore.QTimer.singleShot(0, lambda: self.worker.run(text))

    @QtCore.Slot(DiacritizationResult)
    def _handle_finished(self, result: DiacritizationResult) -> None:
        self.output_edit.setPlainText(result.text)
        self.status_label.setText(
            f"✅ اكتمل باستخدام: {result.model_name}" if result.text else "لم يتم إدخال نص"
        )
        self.statusBar().showMessage(result.model_name)
        self.diacritize_button.setDisabled(False)

    @QtCore.Slot(str)
    def _handle_failed(self, message: str) -> None:
        QtWidgets.QMessageBox.critical(self, "خطأ", message)
        self.status_label.setText("حدث خطأ أثناء المعالجة")
        self.diacritize_button.setDisabled(False)

    @QtCore.Slot(str)
    def _handle_progress(self, message: str) -> None:
        self.status_label.setText(message)

    def _clear_fields(self) -> None:
        self.input_edit.clear()
        self.output_edit.clear()
        self.status_label.setText("جاهز")

    def _copy_output(self) -> None:
        text = self.output_edit.toPlainText()
        QtGui.QGuiApplication.clipboard().setText(text)
        self.status_label.setText("تم نسخ النص المشكّل")

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: N802
        self.thread.quit()
        self.thread.wait(1000)
        super().closeEvent(event)


def main() -> None:
    QtGui.QGuiApplication.setApplicationDisplayName("Arabic Tashkeel")
    app = QtWidgets.QApplication(sys.argv)
    app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    window = TashkeelWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
