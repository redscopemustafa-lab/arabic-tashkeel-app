"""Invoices page."""

from qt_compat import QtWidgets
from ui.dialogs.invoice_dialog import InvoiceDialog


class InvoicesPage(QtWidgets.QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()
        self.load_invoices()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        button_row = QtWidgets.QHBoxLayout()
        add_btn = QtWidgets.QPushButton("New Invoice")
        edit_btn = QtWidgets.QPushButton("Edit Invoice")
        delete_btn = QtWidgets.QPushButton("Delete Invoice")
        add_btn.clicked.connect(self.add_invoice)
        edit_btn.clicked.connect(self.edit_invoice)
        delete_btn.clicked.connect(self.delete_invoice)
        for btn in (add_btn, edit_btn, delete_btn):
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
        for row_idx, invoice in enumerate(invoices):
            self.table.insertRow(row_idx)
            values = [
                invoice["id"],
                invoice["invoice_number"],
                invoice["customer_name"] or "",
                invoice["invoice_date"] or "",
                invoice["due_date"] or "",
                f"{invoice['total_amount'] or 0:.2f}",
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
