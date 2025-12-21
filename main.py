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
from ui.translations import translate

APP_TITLE = "Noura Accounting"


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = get_database(Path("noura_accounting.db"))
        self.settings = self.db.get_settings()
        self.language = self.settings.get("language", "en")
        self.current_page_key = "dashboard"
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
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)
        side_layout = QtWidgets.QVBoxLayout(sidebar)
        side_layout.setContentsMargins(10, 20, 10, 20)
        side_layout.setSpacing(10)
        self.sidebar = sidebar

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
            btn.setStyleSheet(self._nav_button_style())
            btn.clicked.connect(handler)
            self.menu_buttons.append(btn)
            side_layout.addWidget(btn)
        side_layout.addStretch()

        # Main area with top bar
        content_wrapper = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(0, 0, 0, 0)

        top_bar = QtWidgets.QFrame()
        top_bar.setObjectName("topbar")
        top_layout = QtWidgets.QHBoxLayout(top_bar)
        top_layout.setContentsMargins(15, 10, 15, 10)
        self.title_label = QtWidgets.QLabel(self._window_title())
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        content_layout.addWidget(top_bar)
        self.top_bar = top_bar

        self.stack = QtWidgets.QStackedWidget()
        self.dashboard_page = DashboardPage(self.db, self.settings, self.language)
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

    def _nav_button_style(self, active: bool = False) -> str:
        theme = self.settings.get("theme", "dark")
        if theme == "light":
            base = "QPushButton {padding:12px; text-align:left; border:none; background: transparent; color:#1f1f1f;}"
            hover = "QPushButton:hover {background-color: #e1e5ee;}"
        else:
            base = "QPushButton {padding:12px; text-align:left; border:none; background: transparent; color:white;}"
            hover = "QPushButton:hover {background-color: #34495e;}"
        weight = "QPushButton {font-weight:bold;}" if active else ""
        return base + hover + weight

    def _apply_theme(self) -> None:
        theme = self.settings.get("theme", "dark")
        if theme == "light":
            stylesheet = """
            QWidget { background-color: #f5f6fb; color: #1f1f1f; }
            QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
                background-color: #ffffff;
                color: #1f1f1f;
                border: 1px solid #d0d0d0;
                padding: 4px;
            }
            QTableWidget { background-color: #ffffff; color: #1f1f1f; gridline-color: #d0d0d0; }
            QHeaderView::section { background-color: #e8e8e8; color: #1f1f1f; }
            QPushButton { background-color: #e0e0e0; color: #1f1f1f; border: 1px solid #c0c0c0; padding: 8px; }
            QPushButton:hover { background-color: #d5d5d5; }
            """
            sidebar_style = "background-color: #eef0f5; color: #1f1f1f;"
            topbar_style = "background-color: #eef0f5; border-bottom: 1px solid #d0d0d0; color:#1f1f1f;"
        else:
            stylesheet = """
            QWidget { background-color: #121212; color: #ecf0f1; }
            QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
                background-color: #1f1f1f;
                color: #ecf0f1;
                border: 1px solid #3c3c3c;
                padding: 4px;
            }
            QTableWidget { background-color: #1a1a1a; color: #ecf0f1; gridline-color: #2e2e2e; }
            QHeaderView::section { background-color: #1f2a30; color: #ecf0f1; }
            QPushButton { background-color: #34495e; color: white; border: 1px solid #2c3e50; padding: 8px; border-radius: 3px; }
            QPushButton:hover { background-color: #3d566e; }
            """
            sidebar_style = "background-color: #1b2632; color: white;"
            topbar_style = "background-color: #1f2a30; border-bottom: 1px solid #2c3e50; color:#ecf0f1;"

        self.setStyleSheet(stylesheet)
        self.sidebar.setStyleSheet(sidebar_style)
        self.top_bar.setStyleSheet(topbar_style)
        # Refresh navigation button styling per theme
        self._activate_button(self.menu_buttons[self._page_index(self.current_page_key)])

    def _refresh_menu_labels(self) -> None:
        for (key, _handler), btn in zip(self.menu_items, self.menu_buttons):
            btn.setText(translate(self.language, key))
        self._update_title(self.current_page_key)

    # Navigation handlers
    def _activate_button(self, active_btn: QtWidgets.QPushButton):
        for btn in self.menu_buttons:
            btn.setStyleSheet(self._nav_button_style(active_btn is btn))

    def _page_index(self, key: str) -> int:
        for idx, (menu_key, _) in enumerate(self.menu_items):
            if key == menu_key:
                return idx
        return 0

    def _update_title(self, page_key: str):
        page_label = translate(self.language, page_key)
        self.title_label.setText(f"{self._window_title()} — {page_label}")
        self.current_page_key = page_key

    def show_dashboard(self):
        self.stack.setCurrentWidget(self.dashboard_page)
        self.dashboard_page.refresh()
        self._activate_button(self.menu_buttons[0])
        self._update_title("dashboard")

    def show_customers(self):
        self.stack.setCurrentWidget(self.customers_page)
        self.customers_page.load_customers()
        self._activate_button(self.menu_buttons[1])
        self._update_title("customers")

    def show_products(self):
        self.stack.setCurrentWidget(self.products_page)
        self.products_page.load_products()
        self._activate_button(self.menu_buttons[2])
        self._update_title("products")

    def show_invoices(self):
        self.stack.setCurrentWidget(self.invoices_page)
        self.invoices_page.load_invoices()
        self._activate_button(self.menu_buttons[3])
        self._update_title("invoices")

    def show_reports(self):
        self.stack.setCurrentWidget(self.reports_page)
        self.reports_page.refresh()
        self._activate_button(self.menu_buttons[4])
        self._update_title("reports")

    def show_settings(self):
        self.stack.setCurrentWidget(self.settings_page)
        self.settings_page.load_settings()
        self._activate_button(self.menu_buttons[5])
        self._update_title("settings")

    def _on_settings_saved(self, data: dict):
        self.settings = self.db.get_settings()
        self.language = self.settings.get("language", "en")
        self.dashboard_page.update_settings(self.settings, self.language)
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
