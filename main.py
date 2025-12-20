"""Entry point for Noura Accounting desktop app."""

import sys
from pathlib import Path

from qt_compat import QtWidgets, QtGui, QtCore
from database import get_database
from ui.pages.dashboard import DashboardPage
from ui.pages.customers import CustomersPage
from ui.pages.products import ProductsPage
from ui.pages.invoices import InvoicesPage
from ui.pages.reports import ReportsPage
from ui.pages.settings import SettingsPage

APP_TITLE = "Noura Accounting"


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1000, 700)
        self.db = get_database(Path("noura_accounting.db"))
        self._build_ui()

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

        self.menu_buttons = []
        menu_items = [
            ("Dashboard", self.show_dashboard),
            ("Customers", self.show_customers),
            ("Products", self.show_products),
            ("Invoices", self.show_invoices),
            ("Reports", self.show_reports),
            ("Settings", self.show_settings),
        ]
        for label, handler in menu_items:
            btn = QtWidgets.QPushButton(label)
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
        title_label = QtWidgets.QLabel(APP_TITLE)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        content_layout.addWidget(top_bar)

        self.stack = QtWidgets.QStackedWidget()
        self.dashboard_page = DashboardPage(self.db)
        self.customers_page = CustomersPage(self.db)
        self.products_page = ProductsPage(self.db)
        self.invoices_page = InvoicesPage(self.db)
        self.reports_page = ReportsPage(self.db)
        self.settings_page = SettingsPage()

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
        self._activate_button(self.menu_buttons[5])

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
