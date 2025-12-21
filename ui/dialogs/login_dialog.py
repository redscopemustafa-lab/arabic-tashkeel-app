"""Admin login dialog with username/password/license."""

from qt_compat import QtWidgets


class AdminLoginDialog(QtWidgets.QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Admin Login")
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QFormLayout(self)
        self.username_edit = QtWidgets.QLineEdit()
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.license_edit = QtWidgets.QLineEdit()

        layout.addRow("Username", self.username_edit)
        layout.addRow("Password", self.password_edit)
        layout.addRow("License Key", self.license_edit)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._attempt_login)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def _attempt_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        license_key = self.license_edit.text().strip()

        if not username or not password or not license_key:
            QtWidgets.QMessageBox.warning(self, "Login", "Please fill all fields.")
            return

        # Hashing kept for compatibility; the database stores SHA256 in admin_users.
        if self.db.authenticate_admin(username, password, license_key):
            self.accept()
        else:
            QtWidgets.QMessageBox.critical(self, "Login", "Invalid credentials or license key.")
