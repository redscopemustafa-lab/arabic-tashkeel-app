"""Customers page."""

from qt_compat import QtWidgets
from ui.dialogs.customer_dialog import CustomerDialog


class CustomersPage(QtWidgets.QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()
        self.load_customers()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        button_row = QtWidgets.QHBoxLayout()
        add_btn = QtWidgets.QPushButton("Add")
        edit_btn = QtWidgets.QPushButton("Edit")
        delete_btn = QtWidgets.QPushButton("Delete")
        add_btn.clicked.connect(self.add_customer)
        edit_btn.clicked.connect(self.edit_customer)
        delete_btn.clicked.connect(self.delete_customer)
        for btn in (add_btn, edit_btn, delete_btn):
            button_row.addWidget(btn)
        button_row.addStretch()
        layout.addLayout(button_row)

        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Name",
            "Email",
            "Phone",
            "Address",
            "Tax Number",
        ])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def load_customers(self):
        customers = self.db.fetch_customers()
        self.table.setRowCount(0)
        for row_idx, customer in enumerate(customers):
            self.table.insertRow(row_idx)
            for col, key in enumerate(["id", "name", "email", "phone", "address", "tax_number"]):
                item = QtWidgets.QTableWidgetItem(str(customer[key] or ""))
                self.table.setItem(row_idx, col, item)

    def _selected_customer_id(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return int(self.table.item(indexes[0].row(), 0).text())

    def add_customer(self):
        dialog = CustomerDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            data = dialog.get_data()
            self.db.add_customer(data)
            self.load_customers()

    def edit_customer(self):
        customer_id = self._selected_customer_id()
        if not customer_id:
            QtWidgets.QMessageBox.information(self, "Edit Customer", "Please select a customer.")
            return
        row = self.table.selectionModel().selectedRows()[0].row()
        data = {
            "name": self.table.item(row, 1).text(),
            "email": self.table.item(row, 2).text(),
            "phone": self.table.item(row, 3).text(),
            "address": self.table.item(row, 4).text(),
            "tax_number": self.table.item(row, 5).text(),
        }
        dialog = CustomerDialog(self, data)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.db.update_customer(customer_id, dialog.get_data())
            self.load_customers()

    def delete_customer(self):
        customer_id = self._selected_customer_id()
        if not customer_id:
            QtWidgets.QMessageBox.information(self, "Delete Customer", "Please select a customer.")
            return
        confirm = QtWidgets.QMessageBox.question(
            self, "Delete Customer", "Are you sure you want to delete this customer?"
        )
        if confirm == QtWidgets.QMessageBox.Yes:
            self.db.delete_customer(customer_id)
            self.load_customers()
