"""Product/service form dialog."""

from qt_compat import QtWidgets


class ProductDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Product / Service")
        self.data = data or {}
        self._build_ui()
        if data:
            self._load_data(data)

    def _build_ui(self):
        layout = QtWidgets.QFormLayout(self)

        self.name_edit = QtWidgets.QLineEdit()
        self.description_edit = QtWidgets.QPlainTextEdit()
        self.cost_price_spin = QtWidgets.QDoubleSpinBox()
        self.cost_price_spin.setMaximum(1e9)
        self.cost_price_spin.setPrefix("$")
        self.cost_price_spin.setDecimals(2)
        self.cost_price_spin.setValue(0.0)

        self.sale_price_spin = QtWidgets.QDoubleSpinBox()
        self.sale_price_spin.setMaximum(1e9)
        self.sale_price_spin.setPrefix("$")
        self.sale_price_spin.setDecimals(2)
        self.sale_price_spin.setValue(0.0)

        self.stock_spin = QtWidgets.QSpinBox()
        self.stock_spin.setRange(0, 10_000_000)
        self.stock_spin.setValue(0)

        self.unit_edit = QtWidgets.QLineEdit()
        self.unit_edit.setPlaceholderText("e.g. hour, item")

        layout.addRow("Name*", self.name_edit)
        layout.addRow("Description", self.description_edit)
        layout.addRow("Cost Price", self.cost_price_spin)
        layout.addRow("Sale Price", self.sale_price_spin)
        layout.addRow("Stock", self.stock_spin)
        layout.addRow("Unit", self.unit_edit)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

    def _load_data(self, data):
        self.name_edit.setText(data.get("name", ""))
        self.description_edit.setPlainText(data.get("description", ""))
        self.cost_price_spin.setValue(float(data.get("cost_price", 0.0)))
        self.sale_price_spin.setValue(float(data.get("sale_price", data.get("unit_price", 0.0))))
        self.stock_spin.setValue(int(data.get("stock", 0)))
        self.unit_edit.setText(data.get("unit", ""))

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.toPlainText().strip(),
            "unit_price": float(self.sale_price_spin.value()),
            "cost_price": float(self.cost_price_spin.value()),
            "sale_price": float(self.sale_price_spin.value()),
            "stock": int(self.stock_spin.value()),
            "unit": self.unit_edit.text().strip(),
        }

    def accept(self):
        if not self.name_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, "Validation", "Name is required")
            return
        super().accept()
