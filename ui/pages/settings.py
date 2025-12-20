"""Settings page for company info."""

import json
from pathlib import Path

from qt_compat import QtWidgets

SETTINGS_FILE = Path("settings.json")


class SettingsPage(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.load_settings()

    def _build_ui(self):
        layout = QtWidgets.QFormLayout(self)

        self.company_name_edit = QtWidgets.QLineEdit()
        self.company_address_edit = QtWidgets.QPlainTextEdit()
        self.currency_edit = QtWidgets.QLineEdit()

        layout.addRow("Company Name", self.company_name_edit)
        layout.addRow("Company Address", self.company_address_edit)
        layout.addRow("Default Currency", self.currency_edit)

        save_btn = QtWidgets.QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addRow(save_btn)

    def load_settings(self):
        if SETTINGS_FILE.exists():
            data = json.loads(SETTINGS_FILE.read_text())
            self.company_name_edit.setText(data.get("company_name", ""))
            self.company_address_edit.setPlainText(data.get("company_address", ""))
            self.currency_edit.setText(data.get("default_currency", ""))

    def save_settings(self):
        data = {
            "company_name": self.company_name_edit.text().strip(),
            "company_address": self.company_address_edit.toPlainText().strip(),
            "default_currency": self.currency_edit.text().strip(),
        }
        SETTINGS_FILE.write_text(json.dumps(data, indent=2))
        QtWidgets.QMessageBox.information(self, "Settings", "Settings saved successfully.")
