"""Settings page for company info."""

from qt_compat import QtWidgets, QtCore
from ui.translations import translate


class SettingsPage(QtWidgets.QWidget):
    settings_saved = QtCore.Signal(dict)

    def __init__(self, db, language: str = "en", parent=None):
        super().__init__(parent)
        self.db = db
        self.language = language
        self._build_ui()
        self.load_settings()

    def update_language(self, language: str):
        self.language = language
        self._refresh_labels()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.title_label = QtWidgets.QLabel(translate(self.language, "settings"))
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(self.title_label)

        form = QtWidgets.QFormLayout()

        self.company_name_edit = QtWidgets.QLineEdit()
        self.company_phone_edit = QtWidgets.QLineEdit()
        self.company_address_edit = QtWidgets.QTextEdit()
        self.currency_edit = QtWidgets.QLineEdit()

        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItem("Dark", "dark")
        self.theme_combo.addItem("Light", "light")

        self.language_combo = QtWidgets.QComboBox()
        self.language_combo.addItem("Türkçe", "tr")
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Bahasa Indonesia", "id")
        self.language_combo.addItem("العربية", "ar")

        form.addRow(translate(self.language, "company_name"), self.company_name_edit)
        form.addRow(translate(self.language, "company_phone"), self.company_phone_edit)
        form.addRow(translate(self.language, "company_address"), self.company_address_edit)
        form.addRow(translate(self.language, "default_currency"), self.currency_edit)
        form.addRow(translate(self.language, "theme"), self.theme_combo)
        form.addRow(translate(self.language, "language"), self.language_combo)

        save_btn = QtWidgets.QPushButton(translate(self.language, "save_settings"))
        save_btn.clicked.connect(self.save_settings)
        form.addRow(save_btn)
        layout.addLayout(form)

    def _refresh_labels(self):
        form_layout: QtWidgets.QFormLayout = self.layout().itemAt(1).layout()  # type: ignore[assignment]
        form_layout.labelForField(self.company_name_edit).setText(translate(self.language, "company_name"))
        form_layout.labelForField(self.company_phone_edit).setText(translate(self.language, "company_phone"))
        form_layout.labelForField(self.company_address_edit).setText(translate(self.language, "company_address"))
        form_layout.labelForField(self.currency_edit).setText(translate(self.language, "default_currency"))
        form_layout.labelForField(self.theme_combo).setText(translate(self.language, "theme"))
        form_layout.labelForField(self.language_combo).setText(translate(self.language, "language"))
        # Save button is always the last row
        save_button = form_layout.itemAt(form_layout.rowCount() - 1, QtWidgets.QFormLayout.FieldRole).widget()
        if save_button:
            save_button.setText(translate(self.language, "save_settings"))
        self.title_label.setText(translate(self.language, "settings"))

    def load_settings(self):
        data = self.db.get_settings()
        self.company_name_edit.setText(data.get("company_name", ""))
        self.company_phone_edit.setText(data.get("company_phone", ""))
        self.company_address_edit.setPlainText(data.get("company_address", ""))
        self.currency_edit.setText(data.get("default_currency", ""))
        theme = data.get("theme", "dark")
        language = data.get("language", "en")
        self.language = language
        self.theme_combo.setCurrentIndex(self.theme_combo.findData(theme))
        self.language_combo.setCurrentIndex(self.language_combo.findData(language))
        self._refresh_labels()

    def save_settings(self):
        data = {
            "company_name": self.company_name_edit.text().strip(),
            "company_phone": self.company_phone_edit.text().strip(),
            "company_address": self.company_address_edit.toPlainText().strip(),
            "default_currency": self.currency_edit.text().strip() or "USD",
            "theme": self.theme_combo.currentData(),
            "language": self.language_combo.currentData(),
        }
        self.db.save_settings(
            data["company_name"],
            data["company_phone"],
            data["company_address"],
            data["default_currency"],
            data["theme"],
            data["language"],
        )
        self.settings_saved.emit(data)
        QtWidgets.QMessageBox.information(
            self,
            translate(self.language, "save_settings"),
            "Settings saved. Theme or language changes may require an app restart.",
        )
