"""Customer form dialog."""

from qt_compat import QtWidgets


class CustomerDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Customer")
        self.data = data or {}
        self._build_ui()
        if data:
            self._load_data(data)

    def _build_ui(self):
        layout = QtWidgets.QFormLayout(self)

        self.name_edit = QtWidgets.QLineEdit()
        self.email_edit = QtWidgets.QLineEdit()
        self.phone_edit = QtWidgets.QLineEdit()
        self.address_edit = QtWidgets.QPlainTextEdit()
        self.tax_edit = QtWidgets.QLineEdit()

        layout.addRow("Name*", self.name_edit)
        layout.addRow("Email", self.email_edit)
        layout.addRow("Phone", self.phone_edit)
        layout.addRow("Address", self.address_edit)
        layout.addRow("Tax Number", self.tax_edit)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def _load_data(self, data):
        self.name_edit.setText(data.get("name", ""))
        self.email_edit.setText(data.get("email", ""))
        self.phone_edit.setText(data.get("phone", ""))
        self.address_edit.setPlainText(data.get("address", ""))
        self.tax_edit.setText(data.get("tax_number", ""))

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "address": self.address_edit.toPlainText().strip(),
            "tax_number": self.tax_edit.text().strip(),
        }

    def accept(self):
        if not self.name_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, "Validation", "Name is required")
            return
        super().accept()
