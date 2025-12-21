"""Invoices page."""

from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter

from qt_compat import QtWidgets
from ui.dialogs.invoice_dialog import InvoiceDialog
from ui.translations import translate


class InvoicesPage(QtWidgets.QWidget):
    def __init__(self, db, settings: dict | None = None, language: str = "en", parent=None):
        super().__init__(parent)
        self.db = db
        self.settings = settings or {}
        self.language = language
        self._build_ui()
        self.load_invoices()

    def update_settings(self, settings: dict, language: str | None = None):
        self.settings = settings
        if language:
            self.language = language
        self._refresh_labels()
        self.load_invoices()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        self.title_label = QtWidgets.QLabel(translate(self.language, "invoices"))
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(self.title_label)

        button_row = QtWidgets.QHBoxLayout()
        add_btn = QtWidgets.QPushButton(translate(self.language, "new_invoice"))
        edit_btn = QtWidgets.QPushButton(translate(self.language, "edit_invoice"))
        delete_btn = QtWidgets.QPushButton(translate(self.language, "delete_invoice"))
        print_btn = QtWidgets.QPushButton(translate(self.language, "print_export"))
        add_btn.clicked.connect(self.add_invoice)
        edit_btn.clicked.connect(self.edit_invoice)
        delete_btn.clicked.connect(self.delete_invoice)
        print_btn.clicked.connect(self.print_invoice)
        for btn in (add_btn, edit_btn, delete_btn, print_btn):
            button_row.addWidget(btn)
        button_row.addStretch()
        layout.addLayout(button_row)

        self.table = QtWidgets.QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Invoice #",
            "Customer",
            "Invoice Date",
            "Due Date",
            "Total",
            "Status",
        ])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def load_invoices(self):
        invoices = self.db.fetch_invoices()
        self.table.setRowCount(0)
        currency = self.settings.get("default_currency") or ""
        currency_suffix = f" {currency}" if currency else ""
        for row_idx, invoice in enumerate(invoices):
            self.table.insertRow(row_idx)
            values = [
                invoice["id"],
                invoice["invoice_number"],
                invoice["customer_name"] or "",
                invoice["invoice_date"] or "",
                invoice["due_date"] or "",
                f"{invoice['total_amount'] or 0:.2f}{currency_suffix}",
                invoice["status"] or "",
            ]
            for col, value in enumerate(values):
                self.table.setItem(row_idx, col, QtWidgets.QTableWidgetItem(str(value)))

    def _selected_invoice_id(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return int(self.table.item(indexes[0].row(), 0).text())

    def add_invoice(self):
        dialog = InvoiceDialog(self.db, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.load_invoices()

    def edit_invoice(self):
        invoice_id = self._selected_invoice_id()
        if not invoice_id:
            QtWidgets.QMessageBox.information(self, "Edit Invoice", "Please select an invoice.")
            return
        dialog = InvoiceDialog(self.db, self, invoice_id)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.load_invoices()

    def _refresh_labels(self):
        headers = [
            "ID",
            "Invoice #",
            "Customer",
            "Invoice Date",
            "Due Date",
            "Total",
            "Status",
        ]
        self.table.setHorizontalHeaderLabels(headers)
        # Button labels are refreshed on update_settings
        button_layout = self.layout().itemAt(1).layout()
        self.title_label.setText(translate(self.language, "invoices"))
        button_layout.itemAt(0).widget().setText(translate(self.language, "new_invoice"))
        button_layout.itemAt(1).widget().setText(translate(self.language, "edit_invoice"))
        button_layout.itemAt(2).widget().setText(translate(self.language, "delete_invoice"))
        button_layout.itemAt(3).widget().setText(translate(self.language, "print_export"))

    def print_invoice(self):
        invoice_id = self._selected_invoice_id()
        if not invoice_id:
            QtWidgets.QMessageBox.warning(self, "Print Invoice", "Please select an invoice.")
            return

        invoice = self.db.get_invoice_with_items(invoice_id)
        if not invoice:
            QtWidgets.QMessageBox.warning(self, "Print Invoice", "Invoice not found.")
            return

        settings = self.db.get_settings()
        currency = invoice.get("currency") or settings.get("default_currency") or ""
        currency_suffix = f" {currency}" if currency else ""

        filename_suggestion = f"invoice_{invoice.get('number') or invoice_id}.pdf"
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Invoice",
            filename_suggestion,
            "PDF Files (*.pdf)",
        )
        if not filename:
            return

        try:
            if not filename.lower().endswith(".pdf"):
                filename += ".pdf"
            self._export_invoice_to_pdf(invoice, filename, settings, currency_suffix)
            QtWidgets.QMessageBox.information(self, "Export", "Invoice exported as PDF.")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Export", f"Failed to export invoice: {exc}")

    def delete_invoice(self):
        invoice_id = self._selected_invoice_id()
        if not invoice_id:
            QtWidgets.QMessageBox.information(self, "Delete Invoice", "Please select an invoice.")
            return
        confirm = QtWidgets.QMessageBox.question(
            self, "Delete Invoice", "Are you sure you want to delete this invoice?"
        )
        if confirm == QtWidgets.QMessageBox.Yes:
            self.db.delete_invoice(invoice_id)
            self.load_invoices()

    def _export_invoice_to_pdf(self, invoice: dict, filename: str, settings: dict, currency_suffix: str) -> None:
        """Render an invoice to a PDF file using QTextDocument/QPrinter."""

        items_rows = "".join(
            f"<tr><td>{item.get('product_name') or item.get('description') or ''}</td>"
            f"<td>{item.get('quantity')}</td>"
            f"<td>{float(item.get('unit_price') or 0):.2f}{currency_suffix}</td>"
            f"<td>{float(item.get('line_total') or 0):.2f}{currency_suffix}</td></tr>" for item in invoice.get("items", [])
        )

        company_address_html = (settings.get("company_address", "") or "").replace("\n", "<br>")
        customer_address_html = (invoice.get("customer_address") or "").replace("\n", "<br>")

        html = f"""
        <html>
        <head>
        <style>
        body {{ font-family: 'Segoe UI', sans-serif; color: #222; }}
        .header {{ display: flex; justify-content: space-between; align-items: flex-start; }}
        .box {{ padding: 8px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        th {{ background: #f2f2f2; }}
        .total {{ text-align: right; font-size: 18px; margin-top: 12px; }}
        </style>
        </head>
        <body>
            <div class="header">
                <div class="box">
                    <h1>{settings.get('company_name', 'Noura')}</h1>
                    <p>{company_address_html}<br/>{settings.get('company_phone', '')}</p>
                </div>
                <div class="box" style="text-align:right;">
                    <h2>Invoice {invoice.get('number')}</h2>
                    <p>Status: <b>{invoice.get('status') or ''}</b><br/>
                    Date: {invoice.get('date') or ''}<br/>
                    Due: {invoice.get('due_date') or ''}</p>
                </div>
            </div>

            <h3>Bill To</h3>
            <p><b>{invoice.get('customer_name') or ''}</b><br/>{customer_address_html}</p>

            <table>
                <tr><th>Product</th><th>Quantity</th><th>Unit Price</th><th>Total</th></tr>
                {items_rows}
            </table>
            <p class="total"><b>Grand Total: {invoice.get('total') or 0:.2f}{currency_suffix}</b></p>
        </body>
        </html>
        """

        document = QTextDocument()
        document.setHtml(html)
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filename)
        # Qt 6 (PySide6) exposes the print slot as print_ to avoid clashing with
        # the Python keyword; calling it ensures compatibility across versions.
        document.print_(printer)
