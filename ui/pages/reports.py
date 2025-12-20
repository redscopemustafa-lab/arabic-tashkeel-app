"""Reports page showing KPIs."""

from qt_compat import QtWidgets, QtCore


class ReportsPage(QtWidgets.QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.stats_list = QtWidgets.QListWidget()
        layout.addWidget(self.stats_list)
        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(refresh_btn)
        layout.addStretch()

    def refresh(self):
        summary = self.db.totals_summary()
        self.stats_list.clear()
        self.stats_list.addItem(f"Total customers: {summary.get('total_customers', 0)}")
        self.stats_list.addItem(f"Total invoices: {summary.get('total_invoices', 0)}")
        revenue = summary.get("total_revenue") or 0.0
        self.stats_list.addItem(f"Total revenue: {revenue:.2f}")
        self.stats_list.addItem("Status breakdown:")
        for status, amount in summary.get("status_breakdown", {}).items():
            item = QtWidgets.QListWidgetItem(f"  {status}: {amount:.2f}")
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.stats_list.addItem(item)
