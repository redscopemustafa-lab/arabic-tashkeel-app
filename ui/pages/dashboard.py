"""Dashboard page showing quick stats."""

from qt_compat import QtWidgets, QtCore


class DashboardPage(QtWidgets.QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.summary_label = QtWidgets.QLabel()
        self.summary_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.summary_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.summary_label)
        layout.addStretch()

    def refresh(self):
        summary = self.db.totals_summary()
        total_customers = summary.get("total_customers", 0)
        total_invoices = summary.get("total_invoices", 0)
        total_revenue = summary.get("total_revenue") or 0.0
        status_breakdown = summary.get("status_breakdown", {})
        status_lines = "<br>".join(
            f"<b>{status}</b>: {amount:.2f}" for status, amount in status_breakdown.items()
        )
        self.summary_label.setText(
            f"Total customers: <b>{total_customers}</b><br>"
            f"Total invoices: <b>{total_invoices}</b><br>"
            f"Total revenue: <b>{total_revenue:.2f}</b><br><br>"
            f"Status breakdown:<br>{status_lines}"
        )
