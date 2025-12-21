"""Dashboard page showing quick stats."""

from PySide6.QtCharts import QChart, QChartView, QPieSeries

from qt_compat import QtWidgets, QtCore, QtGui


class DashboardPage(QtWidgets.QWidget):
    def __init__(self, db, settings: dict | None = None, parent=None):
        super().__init__(parent)
        self.db = db
        self.settings = settings or {}
        self._build_ui()
        self.refresh()

    def update_settings(self, settings: dict) -> None:
        self.settings = settings

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.summary_label = QtWidgets.QLabel()
        self.summary_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.summary_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.summary_label)

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.chart_view.setMinimumHeight(280)
        layout.addWidget(self.chart_view)
        layout.addStretch()

    def _build_chart(self):
        series = QPieSeries()
        totals = self.db.get_invoice_status_totals()
        if not totals:
            series.append("No Data", 1)
        else:
            for status, amount in totals:
                series.append(status or "Unknown", amount or 0)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Invoice totals by status")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(QtCore.Qt.AlignBottom)
        self.chart_view.setChart(chart)

    def refresh(self):
        summary = self.db.totals_summary()
        total_customers = summary.get("total_customers", 0)
        total_invoices = summary.get("total_invoices", 0)
        total_revenue = summary.get("total_revenue") or 0.0
        currency = self.settings.get("default_currency", "")
        currency_suffix = f" {currency}" if currency else ""
        status_breakdown = summary.get("status_breakdown", {})
        status_lines = "<br>".join(
            f"<b>{status}</b>: {amount:.2f}{currency_suffix}" for status, amount in status_breakdown.items()
        )
        self.summary_label.setText(
            f"Total customers: <b>{total_customers}</b><br>"
            f"Total invoices: <b>{total_invoices}</b><br>"
            f"Total revenue: <b>{total_revenue:.2f}{currency_suffix}</b><br><br>"
            f"Status breakdown:<br>{status_lines}"
        )
        self._build_chart()
