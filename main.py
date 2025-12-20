"""Ghost IDOR Report Helper

A simple desktop GUI application to assist with IDOR testing and reporting.
Uses PySide6 when available, otherwise falls back to PyQt5.
"""
import sys
import importlib.util
from typing import Dict, Tuple

import requests

# Detect which Qt binding is available without wrapping imports in try/except.
if importlib.util.find_spec("PySide6") is not None:
    from PySide6.QtWidgets import (
        QApplication,
        QComboBox,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QPushButton,
        QSizePolicy,
        QTextEdit,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
elif importlib.util.find_spec("PyQt5") is not None:
    from PyQt5.QtWidgets import (
        QApplication,
        QComboBox,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QPushButton,
        QSizePolicy,
        QTextEdit,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
else:
    raise ImportError("Neither PySide6 nor PyQt5 is installed.")


class MainWindow(QMainWindow):
    """Main application window for Ghost IDOR Report Helper."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Ghost IDOR Report Helper")
        self.resize(1200, 700)

        # Stored results for report generation
        self.last_results: Dict[str, Dict[str, str]] = {"A": {}, "B": {}}

        # Build the UI structure
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # Left: input and configuration
        input_layout = QVBoxLayout()
        input_layout.setSpacing(12)
        main_layout.addLayout(input_layout, 3)

        input_layout.addWidget(self._build_target_group())
        input_layout.addWidget(self._build_account_group("A"))
        input_layout.addWidget(self._build_account_group("B"))
        input_layout.addLayout(self._build_button_row())

        # Right: results and reporting
        results_layout = QVBoxLayout()
        results_layout.setSpacing(12)
        main_layout.addLayout(results_layout, 4)

        self.results_table = self._build_results_table()
        results_layout.addWidget(self.results_table)

        self.analysis_box = QTextEdit()
        self.analysis_box.setReadOnly(True)
        self.analysis_box.setPlaceholderText("Analysis and comparison will appear here...")
        results_layout.addWidget(self._wrap_with_label("Analysis", self.analysis_box))

        self.report_box = QTextEdit()
        self.report_box.setReadOnly(True)
        self.report_box.setPlaceholderText("Generate the report snippet to see Markdown output...")
        results_layout.addWidget(self._wrap_with_label("Report Snippet (Markdown)", self.report_box))

    # ------------------------------------------------------------------
    # UI builders
    def _wrap_with_label(self, label_text: str, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(label_text))
        layout.addWidget(widget)
        return container

    def _build_target_group(self) -> QGroupBox:
        group = QGroupBox("Target")
        layout = QVBoxLayout(group)

        self.target_url = QLineEdit()
        self.target_url.setPlaceholderText("https://target.com/api/user/{ACCOUNT_ID}/profile")
        layout.addWidget(self._wrap_with_label("Target URL or Endpoint Template", self.target_url))

        self.method_combo = QComboBox()
        self.method_combo.addItems(["GET", "POST"])
        layout.addWidget(self._wrap_with_label("HTTP Method", self.method_combo))

        self.body_edit = QTextEdit()
        self.body_edit.setPlaceholderText("Raw body (optional, used for POST requests)...")
        layout.addWidget(self._wrap_with_label("Body (optional)", self.body_edit))

        self.common_headers_edit = QTextEdit()
        self.common_headers_edit.setPlaceholderText("Common headers (one per line, e.g. User-Agent: BugBountyTester)")
        layout.addWidget(self._wrap_with_label("Common headers (optional)", self.common_headers_edit))
        return group

    def _build_account_group(self, account_label: str) -> QGroupBox:
        group = QGroupBox(f"Account {account_label}")
        layout = QVBoxLayout(group)

        line_edit = QLineEdit()
        line_edit.setPlaceholderText(f"Account {account_label} ID")
        if account_label == "A":
            self.account_a_id = line_edit
        else:
            self.account_b_id = line_edit
        layout.addWidget(self._wrap_with_label(f"Account {account_label} ID", line_edit))

        headers_edit = QTextEdit()
        headers_edit.setPlaceholderText("Headers override (one per line, e.g. Cookie: session=...)")
        if account_label == "A":
            self.account_a_headers = headers_edit
        else:
            self.account_b_headers = headers_edit
        layout.addWidget(self._wrap_with_label("Headers override (optional)", headers_edit))
        return group

    def _build_button_row(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        self.run_button = QPushButton("Run Test")
        self.run_button.clicked.connect(self.run_test)
        layout.addWidget(self.run_button)

        self.clear_button = QPushButton("Clear Results")
        self.clear_button.clicked.connect(self.clear_results)
        layout.addWidget(self.clear_button)

        self.report_button = QPushButton("Generate Report Snippet")
        self.report_button.clicked.connect(self.generate_report)
        layout.addWidget(self.report_button)

        layout.addStretch()
        return layout

    def _build_results_table(self) -> QTableWidget:
        table = QTableWidget(2, 5)
        table.setHorizontalHeaderLabels(["Account", "Final URL", "Status", "Length", "Preview (first 300 chars)"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        table.setItem(0, 0, QTableWidgetItem("A"))
        table.setItem(1, 0, QTableWidgetItem("B"))
        return table

    # ------------------------------------------------------------------
    # Utility helpers
    def parse_headers(self, text: str) -> Dict[str, str]:
        """Parse user-provided header lines into a dictionary."""
        headers: Dict[str, str] = {}
        for line in text.splitlines():
            if not line.strip():
                continue
            key, sep, value = line.partition(":")
            if not sep:
                # Invalid line; ignore it but keep UI responsive
                continue
            headers[key.strip()] = value.strip()
        return headers

    def build_headers(self, common: Dict[str, str], overrides: Dict[str, str]) -> Dict[str, str]:
        """Merge common headers with account-specific overrides."""
        merged = dict(common)
        merged.update(overrides)
        return merged

    def prepare_url(self, template: str, account_id: str) -> str:
        """Replace placeholder with the provided account id when present."""
        if "{ACCOUNT_ID}" in template:
            return template.replace("{ACCOUNT_ID}", account_id)
        return template

    def perform_request(self, method: str, url: str, headers: Dict[str, str], body: str) -> Tuple[str, str, str]:
        """Execute the HTTP request and return status, length, and preview."""
        session = requests.Session()
        try:
            if method == "POST":
                response = session.post(url, headers=headers, data=body)
            else:
                response = session.get(url, headers=headers)
            status = str(response.status_code)
            text = response.text
            length = str(len(text))
            preview = text[:300]
            return status, length, preview
        except requests.RequestException as exc:  # Capture network-related errors
            error_msg = f"Error: {exc}"
            return error_msg, "0", error_msg[:300]

    # ------------------------------------------------------------------
    # Actions
    def run_test(self) -> None:
        """Run the IDOR test for both accounts and populate the UI."""
        url_template = self.target_url.text().strip()
        method = self.method_combo.currentText().upper()
        body = self.body_edit.toPlainText()

        common_headers = self.parse_headers(self.common_headers_edit.toPlainText())
        a_headers = self.build_headers(common_headers, self.parse_headers(self.account_a_headers.toPlainText()))
        b_headers = self.build_headers(common_headers, self.parse_headers(self.account_b_headers.toPlainText()))

        account_a_id = self.account_a_id.text().strip()
        account_b_id = self.account_b_id.text().strip()

        url_a = self.prepare_url(url_template, account_a_id)
        url_b = self.prepare_url(url_template, account_b_id)

        status_a, length_a, preview_a = self.perform_request(method, url_a, a_headers, body)
        status_b, length_b, preview_b = self.perform_request(method, url_b, b_headers, body)

        self.last_results["A"] = {
            "url": url_a,
            "status": status_a,
            "length": length_a,
            "preview": preview_a,
            "headers": a_headers,
            "method": method,
        }
        self.last_results["B"] = {
            "url": url_b,
            "status": status_b,
            "length": length_b,
            "preview": preview_b,
            "headers": b_headers,
            "method": method,
        }

        # Populate table
        self._populate_table_row(0, self.last_results["A"])
        self._populate_table_row(1, self.last_results["B"])

        # Update analysis
        self.analysis_box.setPlainText(self.generate_analysis())

    def _populate_table_row(self, row: int, data: Dict[str, str]) -> None:
        self.results_table.setItem(row, 1, QTableWidgetItem(data.get("url", "")))
        self.results_table.setItem(row, 2, QTableWidgetItem(data.get("status", "")))
        self.results_table.setItem(row, 3, QTableWidgetItem(data.get("length", "")))
        self.results_table.setItem(row, 4, QTableWidgetItem(data.get("preview", "")))

    def generate_analysis(self) -> str:
        """Create a basic analysis summary comparing both responses."""
        status_a = self.last_results["A"].get("status", "")
        status_b = self.last_results["B"].get("status", "")
        length_a = self.last_results["A"].get("length", "0")
        length_b = self.last_results["B"].get("length", "0")

        # If errors occurred
        if status_a.startswith("Error") or status_b.startswith("Error"):
            return "One or more requests encountered errors. Please verify connectivity and headers."

        # Compare statuses and lengths for quick guidance
        if status_a == status_b == "200" and length_a == length_b:
            return (
                "Both A and B received HTTP 200 with identical response lengths. "
                "This may indicate that Account B can access Account A's data. Please manually review the contents."
            )
        if status_a == "200" and status_b == "200":
            return (
                "Both requests returned 200 but response lengths differ. Manual inspection is required to confirm whether "
                "Account B can access Account A data."
            )
        if status_a == "200" and status_b.startswith("4"):
            return "Account A succeeded while Account B was denied. Access control appears to be enforced."
        if status_a.startswith("4") and status_b == "200":
            return (
                "Account B succeeded while Account A failed. This is unusual and should be investigated for potential misconfiguration."
            )
        return "Account A and B responses differ. Further manual analysis is required."

    def clear_results(self) -> None:
        """Reset displayed results and stored data."""
        self.last_results = {"A": {}, "B": {}}
        for row in range(2):
            for col in range(1, 5):
                self.results_table.setItem(row, col, QTableWidgetItem(""))
        self.analysis_box.clear()
        self.report_box.clear()

    def generate_report(self) -> None:
        """Generate a Markdown snippet summarizing the test."""
        if not self.last_results["A"] or not self.last_results["B"]:
            self.report_box.setPlainText("Run a test first to generate a report snippet.")
            return

        target_display = self.target_url.text().strip() or "[Not provided]"
        account_a_id = self.account_a_id.text().strip() or "[Not provided]"
        account_b_id = self.account_b_id.text().strip() or "[Not provided]"
        method = self.last_results["A"].get("method", "GET")

        snippet_lines = [
            f"# Potential IDOR on {target_display}",
            "",
            "## Tested Accounts",
            f"- Account A ID: {account_a_id}",
            f"- Account B ID: {account_b_id}",
            "",
            "## Request Details",
            f"- HTTP Method: {method}",
            f"- Request as Account A: {method} {self.last_results['A'].get('url', '')}",
            f"  - Headers: {self.last_results['A'].get('headers', {})}",
            f"- Request as Account B: {method} {self.last_results['B'].get('url', '')}",
            f"  - Headers: {self.last_results['B'].get('headers', {})}",
            "",
            "## Observed Results",
            f"- Account A: status {self.last_results['A'].get('status', '')}, length {self.last_results['A'].get('length', '')}",
            f"- Account B: status {self.last_results['B'].get('status', '')}, length {self.last_results['B'].get('length', '')}",
            "",
            "## Impact (to validate)",
            (
                "If confirmed, this issue allows an authenticated user (Account B) to access data "
                "belonging to another user (Account A) by manipulating the ACCOUNT_ID in the URL."
            ),
            "",
            "## Notes",
            "Further manual validation is required to confirm exposure and data sensitivity.",
        ]
        self.report_box.setPlainText("\n".join(snippet_lines))


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
