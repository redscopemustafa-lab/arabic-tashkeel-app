"""Invoice creation/edit dialog."""

import datetime
from typing import List, Dict, Optional

from qt_compat import QtWidgets, QtCore


class InvoiceDialog(QtWidgets.QDialog):
    def __init__(self, db, parent=None, invoice_id: Optional[int] = None):
        super().__init__(parent)
        self.db = db
        self.invoice_id = invoice_id
        self.setWindowTitle("Invoice")
        self.products = {p["id"]: p for p in self.db.fetch_products()}
        self._build_ui()
        self._load_customers()
        self._load_products()
        if invoice_id:
            self._load_invoice(invoice_id)
        else:
            self.invoice_number_edit.setText(self._generate_invoice_number())

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        form_layout = QtWidgets.QGridLayout()
        self.invoice_number_edit = QtWidgets.QLineEdit()
        self.customer_combo = QtWidgets.QComboBox()
        self.invoice_date_edit = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.invoice_date_edit.setCalendarPopup(True)
        self.due_date_edit = QtWidgets.QDateEdit(QtCore.QDate.currentDate().addDays(7))
        self.due_date_edit.setCalendarPopup(True)
        self.status_combo = QtWidgets.QComboBox()
        self.status_combo.addItems(["Draft", "Unpaid", "Paid", "Overdue"])

        form_layout.addWidget(QtWidgets.QLabel("Invoice #"), 0, 0)
        form_layout.addWidget(self.invoice_number_edit, 0, 1)
        form_layout.addWidget(QtWidgets.QLabel("Customer"), 0, 2)
        form_layout.addWidget(self.customer_combo, 0, 3)
        form_layout.addWidget(QtWidgets.QLabel("Invoice Date"), 1, 0)
        form_layout.addWidget(self.invoice_date_edit, 1, 1)
        form_layout.addWidget(QtWidgets.QLabel("Due Date"), 1, 2)
        form_layout.addWidget(self.due_date_edit, 1, 3)
        form_layout.addWidget(QtWidgets.QLabel("Status"), 2, 0)
        form_layout.addWidget(self.status_combo, 2, 1)
        layout.addLayout(form_layout)

        # Items table
        self.items_table = QtWidgets.QTableWidget(0, 5)
        self.items_table.setHorizontalHeaderLabels([
            "Product",
            "Description",
            "Quantity",
            "Unit Price",
            "Line Total",
        ])
        self.items_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.items_table)

        btn_row = QtWidgets.QHBoxLayout()
        add_row_btn = QtWidgets.QPushButton("Add Item")
        remove_row_btn = QtWidgets.QPushButton("Remove Selected")
        add_row_btn.clicked.connect(self.add_item_row)
        remove_row_btn.clicked.connect(self.remove_selected_row)
        btn_row.addWidget(add_row_btn)
        btn_row.addWidget(remove_row_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        totals_layout = QtWidgets.QHBoxLayout()
        totals_layout.addStretch()
        self.total_label = QtWidgets.QLabel("Total: 0.00")
        totals_layout.addWidget(self.total_label)
        layout.addLayout(totals_layout)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._save_invoice)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # start with one row
        self.add_item_row()

    def _generate_invoice_number(self) -> str:
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"INV-{timestamp}"

    def _load_customers(self) -> None:
        self.customer_combo.clear()
        customers = self.db.fetch_customers()
        for c in customers:
            self.customer_combo.addItem(c["name"], c["id"])

    def _load_products(self) -> None:
        # already stored in self.products
        pass

    def add_item_row(self, product_id: Optional[int] = None, description: str = "", quantity: float = 1.0, unit_price: float = 0.0):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        product_combo = QtWidgets.QComboBox()
        product_combo.addItem("Custom item", None)
        for pid, product in self.products.items():
            product_combo.addItem(product["name"], pid)
        if product_id:
            index = product_combo.findData(product_id)
            if index >= 0:
                product_combo.setCurrentIndex(index)
        product_combo.currentIndexChanged.connect(lambda _=None, r=row: self._sync_product_row(r))

        desc_edit = QtWidgets.QLineEdit(description)
        qty_spin = QtWidgets.QDoubleSpinBox()
        qty_spin.setMaximum(1e6)
        qty_spin.setDecimals(2)
        qty_spin.setValue(quantity)
        price_spin = QtWidgets.QDoubleSpinBox()
        price_spin.setMaximum(1e9)
        price_spin.setDecimals(2)
        price_spin.setValue(unit_price)

        for widget in (qty_spin, price_spin):
            widget.valueChanged.connect(self.recalculate_totals)
        desc_edit.textChanged.connect(self.recalculate_totals)

        self.items_table.setCellWidget(row, 0, product_combo)
        self.items_table.setCellWidget(row, 1, desc_edit)
        self.items_table.setCellWidget(row, 2, qty_spin)
        self.items_table.setCellWidget(row, 3, price_spin)

        line_total_item = QtWidgets.QTableWidgetItem("0.00")
        line_total_item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        self.items_table.setItem(row, 4, line_total_item)

        self._sync_product_row(row)

    def remove_selected_row(self):
        selected = self.items_table.selectionModel().selectedRows()
        for index in sorted(selected, key=lambda x: x.row(), reverse=True):
            self.items_table.removeRow(index.row())
        self.recalculate_totals()

    def _sync_product_row(self, row: int):
        product_combo: QtWidgets.QComboBox = self.items_table.cellWidget(row, 0)
        desc_edit: QtWidgets.QLineEdit = self.items_table.cellWidget(row, 1)
        price_spin: QtWidgets.QDoubleSpinBox = self.items_table.cellWidget(row, 3)
        product_id = product_combo.currentData()
        if product_id is not None and product_id in self.products:
            product = self.products[product_id]
            desc_edit.setText(product["description"] or product["name"])
            price_spin.setValue(float(product["unit_price"]))
        self.recalculate_totals()

    def recalculate_totals(self):
        total = 0.0
        for row in range(self.items_table.rowCount()):
            qty_widget: QtWidgets.QDoubleSpinBox = self.items_table.cellWidget(row, 2)
            price_widget: QtWidgets.QDoubleSpinBox = self.items_table.cellWidget(row, 3)
            qty = float(qty_widget.value()) if qty_widget else 0.0
            price = float(price_widget.value()) if price_widget else 0.0
            line_total = qty * price
            total += line_total
            item = self.items_table.item(row, 4)
            if item:
                item.setText(f"{line_total:.2f}")
        self.total_label.setText(f"Total: {total:.2f}")

    def _collect_items(self) -> List[Dict[str, any]]:
        items: List[Dict[str, any]] = []
        for row in range(self.items_table.rowCount()):
            product_combo: QtWidgets.QComboBox = self.items_table.cellWidget(row, 0)
            desc_edit: QtWidgets.QLineEdit = self.items_table.cellWidget(row, 1)
            qty_widget: QtWidgets.QDoubleSpinBox = self.items_table.cellWidget(row, 2)
            price_widget: QtWidgets.QDoubleSpinBox = self.items_table.cellWidget(row, 3)
            description = desc_edit.text().strip()
            qty = float(qty_widget.value()) if qty_widget else 0.0
            price = float(price_widget.value()) if price_widget else 0.0
            if not description and product_combo.currentData() is None:
                # skip empty rows
                continue
            items.append(
                {
                    "product_id": product_combo.currentData(),
                    "description": description or product_combo.currentText(),
                    "quantity": qty,
                    "unit_price": price,
                    "line_total": qty * price,
                }
            )
        return items

    def _load_invoice(self, invoice_id: int):
        invoice = self.db.get_invoice(invoice_id)
        if not invoice:
            return
        self.invoice_number_edit.setText(invoice["invoice_number"])
        customer_index = self.customer_combo.findData(invoice["customer_id"])
        if customer_index >= 0:
            self.customer_combo.setCurrentIndex(customer_index)
        if invoice["invoice_date"]:
            self.invoice_date_edit.setDate(QtCore.QDate.fromString(invoice["invoice_date"], "yyyy-MM-dd"))
        if invoice["due_date"]:
            self.due_date_edit.setDate(QtCore.QDate.fromString(invoice["due_date"], "yyyy-MM-dd"))
        status_index = self.status_combo.findText(invoice["status"] or "")
        if status_index >= 0:
            self.status_combo.setCurrentIndex(status_index)

        items = self.db.fetch_invoice_items(invoice_id)
        self.items_table.setRowCount(0)
        for item in items:
            self.add_item_row(
                product_id=item["product_id"],
                description=item["description"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
            )
        self.recalculate_totals()

    def _save_invoice(self):
        items = self._collect_items()
        if not items:
            QtWidgets.QMessageBox.warning(self, "Validation", "Please add at least one item")
            return

        customer_id = self.customer_combo.currentData()
        invoice_data = {
            "invoice_number": self.invoice_number_edit.text().strip(),
            "customer_id": customer_id,
            "invoice_date": self.invoice_date_edit.date().toString("yyyy-MM-dd"),
            "due_date": self.due_date_edit.date().toString("yyyy-MM-dd"),
            "status": self.status_combo.currentText(),
            "total_amount": sum(item["line_total"] for item in items),
        }

        try:
            if self.invoice_id:
                self.db.update_invoice(self.invoice_id, invoice_data, items)
            else:
                self.db.add_invoice(invoice_data, items)
        except ValueError as exc:  # Stock validation error
            QtWidgets.QMessageBox.warning(self, "Stock", str(exc))
            return
        except Exception as exc:  # Generic DB error
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save invoice: {exc}")
            return

        self.accept()
