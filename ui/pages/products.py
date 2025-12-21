"""Products and services page."""

from qt_compat import QtWidgets
from ui.dialogs.product_dialog import ProductDialog
from ui.translations import translate


class ProductsPage(QtWidgets.QWidget):
    def __init__(self, db, language: str = "en", parent=None):
        super().__init__(parent)
        self.db = db
        self.language = language
        self._build_ui()
        self.load_products()

    def update_language(self, language: str):
        self.language = language
        self._refresh_labels()
        self.load_products()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        self.title_label = QtWidgets.QLabel(translate(self.language, "products"))
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(self.title_label)

        button_row = QtWidgets.QHBoxLayout()
        add_btn = QtWidgets.QPushButton(translate(self.language, "add"))
        edit_btn = QtWidgets.QPushButton(translate(self.language, "edit"))
        delete_btn = QtWidgets.QPushButton(translate(self.language, "delete"))
        add_btn.clicked.connect(self.add_product)
        edit_btn.clicked.connect(self.edit_product)
        delete_btn.clicked.connect(self.delete_product)
        for btn in (add_btn, edit_btn, delete_btn):
            button_row.addWidget(btn)
        button_row.addStretch()
        layout.addLayout(button_row)

        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Name",
            "Description",
            "Unit Price",
            translate(self.language, "stock"),
            "Unit",
        ])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def _refresh_labels(self):
        headers = [
            "ID",
            "Name",
            "Description",
            "Unit Price",
            translate(self.language, "stock"),
            "Unit",
        ]
        self.table.setHorizontalHeaderLabels(headers)
        button_row = self.layout().itemAt(1).layout()
        self.title_label.setText(translate(self.language, "products"))
        button_row.itemAt(0).widget().setText(translate(self.language, "add"))
        button_row.itemAt(1).widget().setText(translate(self.language, "edit"))
        button_row.itemAt(2).widget().setText(translate(self.language, "delete"))

    def load_products(self):
        products = self.db.fetch_products()
        self.table.setRowCount(0)
        for row_idx, product in enumerate(products):
            self.table.insertRow(row_idx)
            for col, key in enumerate(["id", "name", "description", "unit_price", "stock", "unit"]):
                item = QtWidgets.QTableWidgetItem(str(product[key] or ""))
                self.table.setItem(row_idx, col, item)

    def _selected_product_id(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return int(self.table.item(indexes[0].row(), 0).text())

    def add_product(self):
        dialog = ProductDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.db.add_product(dialog.get_data())
            self.load_products()

    def edit_product(self):
        product_id = self._selected_product_id()
        if not product_id:
            QtWidgets.QMessageBox.information(self, "Edit Product", "Please select a product.")
            return
        row = self.table.selectionModel().selectedRows()[0].row()
        data = {
            "name": self.table.item(row, 1).text(),
            "description": self.table.item(row, 2).text(),
            "unit_price": float(self.table.item(row, 3).text() or 0),
            "stock": int(self.table.item(row, 4).text() or 0),
            "unit": self.table.item(row, 5).text(),
        }
        dialog = ProductDialog(self, data)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.db.update_product(product_id, dialog.get_data())
            self.load_products()

    def delete_product(self):
        product_id = self._selected_product_id()
        if not product_id:
            QtWidgets.QMessageBox.information(self, "Delete Product", "Please select a product.")
            return
        confirm = QtWidgets.QMessageBox.question(
            self, "Delete Product", "Are you sure you want to delete this product?"
        )
        if confirm == QtWidgets.QMessageBox.Yes:
            self.db.delete_product(product_id)
            self.load_products()
