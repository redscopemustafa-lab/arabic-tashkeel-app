"""Standalone admin panel window for settings and product management."""

from qt_compat import QtWidgets, QtCore

from ui.pages.settings import SettingsPage
from ui.pages.products import ProductsPage
from ui.translations import translate


class AdminPanelWindow(QtWidgets.QMainWindow):
    settings_updated = QtCore.Signal()

    def __init__(self, db, language: str = "en", parent=None):
        super().__init__(parent)
        self.db = db
        self.language = language
        self.setWindowTitle("Admin Panel")
        self.resize(900, 650)
        self._build_ui()

    def _build_ui(self):
        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)

        tabs = QtWidgets.QTabWidget()

        # Settings tab (reused from previous settings page)
        self.settings_page = SettingsPage(self.db, self.language)
        self.settings_page.settings_saved.connect(self.settings_updated)
        tabs.addTab(self.settings_page, translate(self.language, "settings"))

        # Products tab (admin-only management)
        self.products_page = ProductsPage(self.db, self.language)
        tabs.addTab(self.products_page, translate(self.language, "products"))

        layout.addWidget(tabs)
        self.setCentralWidget(central)

    def closeEvent(self, event):  # type: ignore[override]
        # Refresh DB-backed data when admin closes the panel
        self.settings_updated.emit()
        super().closeEvent(event)
