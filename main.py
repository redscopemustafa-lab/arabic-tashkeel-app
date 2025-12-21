"""Entry point for Noura Accounting desktop app."""

import sys
from pathlib import Path

from qt_compat import QtWidgets, QtGui
from database import get_database
from ui.pages.dashboard import DashboardPage
from ui.pages.customers import CustomersPage
from ui.pages.products import ProductsPage
from ui.pages.invoices import InvoicesPage
from ui.pages.reports import ReportsPage
from ui.pages.settings import SettingsPage
from ui.translations import translate

APP_TITLE = "Noura Accounting"


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = get_database(Path("noura_accounting.db"))
        self.settings = self.db.get_settings()
        self.language = self.settings.get("language", "en")
        self.setWindowTitle(self._window_title())
        self.resize(1000, 700)
        self._build_ui()
        self._apply_theme()

    def _build_ui(self):
        central = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        sidebar = QtWidgets.QFrame()
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet("background-color: #2c3e50; color: white;")
        side_layout = QtWidgets.QVBoxLayout(sidebar)
        side_layout.setContentsMargins(10, 20, 10, 20)
        side_layout.setSpacing(10)

        self.menu_buttons: list[QtWidgets.QPushButton] = []
        self.menu_items = [
            ("dashboard", self.show_dashboard),
            ("customers", self.show_customers),
            ("products", self.show_products),
            ("invoices", self.show_invoices),
            ("reports", self.show_reports),
            ("settings", self.show_settings),
        ]
        for key, handler in self.menu_items:
            btn = QtWidgets.QPushButton(translate(self.language, key))
            btn.setStyleSheet(
                "QPushButton {padding:12px; text-align:left; border:none; background: transparent; color:white;}"
                "QPushButton:hover {background-color: #34495e;}"
            )
            btn.clicked.connect(handler)
            self.menu_buttons.append(btn)
            side_layout.addWidget(btn)
        side_layout.addStretch()

        # Main area with top bar
        content_wrapper = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(0, 0, 0, 0)

        top_bar = QtWidgets.QFrame()
        top_bar.setStyleSheet("background-color: #ecf0f1; border-bottom: 1px solid #bdc3c7;")
        top_layout = QtWidgets.QHBoxLayout(top_bar)
        self.title_label = QtWidgets.QLabel(self._window_title())
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        content_layout.addWidget(top_bar)

        self.stack = QtWidgets.QStackedWidget()
        self.dashboard_page = DashboardPage(self.db, self.settings)
        self.customers_page = CustomersPage(self.db)
        self.products_page = ProductsPage(self.db, self.language)
        self.invoices_page = InvoicesPage(self.db, self.settings, self.language)
        self.reports_page = ReportsPage(self.db)
        self.settings_page = SettingsPage(self.db, self.language)
        self.settings_page.settings_saved.connect(self._on_settings_saved)

        for page in (
            self.dashboard_page,
            self.customers_page,
            self.products_page,
            self.invoices_page,
            self.reports_page,
            self.settings_page,
        ):
            self.stack.addWidget(page)

        content_layout.addWidget(self.stack)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_wrapper)

        self.setCentralWidget(central)
        self.show_dashboard()

    def _window_title(self) -> str:
        company = self.settings.get("company_name") or "Noura"
        return f"{company} - {APP_TITLE}"

    def _apply_theme(self) -> None:
        theme = self.settings.get("theme", "dark")
        if theme == "light":
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#f5f6fa"))
            palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("#2c3e50"))
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor("#ffffff"))
            palette.setColor(QtGui.QPalette.Text, QtGui.QColor("#2c3e50"))
            self.setPalette(palette)
        else:
            self.setPalette(self.style().standardPalette())

    def _refresh_menu_labels(self) -> None:
        for (key, _handler), btn in zip(self.menu_items, self.menu_buttons):
            btn.setText(translate(self.language, key))
        self.title_label.setText(self._window_title())

    # Navigation handlers
    def _activate_button(self, active_btn: QtWidgets.QPushButton):
        for btn in self.menu_buttons:
            btn.setStyleSheet(
                "QPushButton {padding:12px; text-align:left; border:none; background: transparent; color:white;}"
                "QPushButton:hover {background-color: #34495e;}"
                + ("QPushButton {font-weight:bold;}" if btn is active_btn else "")
            )

    def show_dashboard(self):
        self.stack.setCurrentWidget(self.dashboard_page)
        self.dashboard_page.refresh()
        self._activate_button(self.menu_buttons[0])

    def show_customers(self):
        self.stack.setCurrentWidget(self.customers_page)
        self.customers_page.load_customers()
        self._activate_button(self.menu_buttons[1])

    def show_products(self):
        self.stack.setCurrentWidget(self.products_page)
        self.products_page.load_products()
        self._activate_button(self.menu_buttons[2])

    def show_invoices(self):
        self.stack.setCurrentWidget(self.invoices_page)
        self.invoices_page.load_invoices()
        self._activate_button(self.menu_buttons[3])

    def show_reports(self):
        self.stack.setCurrentWidget(self.reports_page)
        self.reports_page.refresh()
        self._activate_button(self.menu_buttons[4])

    def show_settings(self):
        self.stack.setCurrentWidget(self.settings_page)
        self.settings_page.load_settings()
        self._activate_button(self.menu_buttons[5])

    def _on_settings_saved(self, data: dict):
        self.settings = self.db.get_settings()
        self.language = self.settings.get("language", "en")
        self.dashboard_page.update_settings(self.settings)
        self.invoices_page.update_settings(self.settings, self.language)
        self.products_page.update_language(self.language)
        self.settings_page.update_language(self.language)
        self._refresh_menu_labels()
        self.setWindowTitle(self._window_title())
        self._apply_theme()

    def closeEvent(self, event: QtGui.QCloseEvent):  # type: ignore[override]
        self.db.close()
        super().closeEvent(event)


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
