"""Tkinter tabanlı modern muhasebe takip uygulaması."""

from __future__ import annotations

import csv
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from database import DatabaseManager, TransactionRecord, get_database

APP_TITLE = "Muhasebe Takip Programı"
DEFAULT_CATEGORIES = [
    "Maaş",
    "Kira",
    "Fatura",
    "Alışveriş",
    "Yemek",
    "Ulaşım",
    "Eğlence",
    "Sağlık",
    "Yatırım",
    "Diğer",
]
DATE_FILTERS = ["Bugün", "Bu Ay", "Tümü"]


class MuhasebeProgrami:
    """Desktop app for income/expense tracking with SQLite persistence."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1280x820")
        self.root.minsize(1100, 760)

        self.db: DatabaseManager = get_database(Path("muhasebe.db"))
        self.filtered_records: list[TransactionRecord] = []
        self.tree_index_map: dict[str, int] = {}

        self._configure_theme()
        self._create_variables()
        self._build_ui()
        self.refresh_all_views()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _configure_theme(self) -> None:
        """Configure a dark ttk theme."""
        colors = {
            "bg": "#10151c",
            "panel": "#18202b",
            "card": "#1f2937",
            "accent": "#3b82f6",
            "accent_hover": "#2563eb",
            "text": "#f3f4f6",
            "muted": "#9ca3af",
            "success": "#22c55e",
            "danger": "#ef4444",
            "warning": "#f59e0b",
            "border": "#334155",
            "field": "#0f172a",
        }
        self.colors = colors
        self.root.configure(bg=colors["bg"])

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=colors["bg"], foreground=colors["text"])
        style.configure(
            "TFrame", background=colors["bg"], foreground=colors["text"]
        )
        style.configure(
            "Card.TFrame", background=colors["card"], borderwidth=1, relief="solid"
        )
        style.configure(
            "TLabel", background=colors["bg"], foreground=colors["text"], font=("Segoe UI", 10)
        )
        style.configure(
            "Card.TLabel", background=colors["card"], foreground=colors["text"], font=("Segoe UI", 10)
        )
        style.configure(
            "Header.TLabel",
            background=colors["card"],
            foreground=colors["text"],
            font=("Segoe UI Semibold", 13),
        )
        style.configure(
            "MetricTitle.TLabel",
            background=colors["card"],
            foreground=colors["muted"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "MetricValue.TLabel",
            background=colors["card"],
            foreground=colors["text"],
            font=("Segoe UI Semibold", 18),
        )
        style.configure(
            "TNotebook", background=colors["bg"], borderwidth=0
        )
        style.configure(
            "TNotebook.Tab",
            background=colors["panel"],
            foreground=colors["muted"],
            padding=(16, 10),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", colors["card"])],
            foreground=[("selected", colors["text"])],
        )
        style.configure(
            "TButton",
            background=colors["accent"],
            foreground=colors["text"],
            borderwidth=0,
            focusthickness=0,
            padding=(14, 8),
            font=("Segoe UI Semibold", 10),
        )
        style.map(
            "TButton",
            background=[("active", colors["accent_hover"])],
            foreground=[("active", colors["text"])],
        )
        style.configure(
            "Danger.TButton", background=colors["danger"], foreground=colors["text"]
        )
        style.map("Danger.TButton", background=[("active", "#dc2626")])
        style.configure(
            "Secondary.TButton", background=colors["panel"], foreground=colors["text"]
        )
        style.map("Secondary.TButton", background=[("active", colors["card"])])
        style.configure(
            "TEntry",
            fieldbackground=colors["field"],
            foreground=colors["text"],
            insertcolor=colors["text"],
            bordercolor=colors["border"],
        )
        style.configure(
            "TCombobox",
            fieldbackground=colors["field"],
            background=colors["field"],
            foreground=colors["text"],
            arrowcolor=colors["text"],
            bordercolor=colors["border"],
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", colors["field"])],
            selectbackground=[("readonly", colors["field"])],
            selectforeground=[("readonly", colors["text"])],
        )
        style.configure(
            "Treeview",
            background=colors["field"],
            fieldbackground=colors["field"],
            foreground=colors["text"],
            rowheight=30,
            bordercolor=colors["border"],
        )
        style.map("Treeview", background=[("selected", colors["accent"])])
        style.configure(
            "Treeview.Heading",
            background=colors["panel"],
            foreground=colors["text"],
            font=("Segoe UI Semibold", 10),
        )
        style.configure(
            "TLabelframe",
            background=colors["card"],
            foreground=colors["text"],
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "TLabelframe.Label",
            background=colors["card"],
            foreground=colors["text"],
            font=("Segoe UI Semibold", 11),
        )

    def _create_variables(self) -> None:
        """Initialize Tk variables."""
        self.tip_var = tk.StringVar(value="gelir")
        self.tutar_var = tk.StringVar()
        self.kategori_var = tk.StringVar()
        self.aciklama_var = tk.StringVar()
        self.tarih_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.tarih_filtre_var = tk.StringVar(value="Tümü")
        self.kategori_filtre_var = tk.StringVar(value="Tümü")
        self.status_var = tk.StringVar(value="Hazır")

    def _build_ui(self) -> None:
        """Create main layout and widgets."""
        self._build_menu()

        container = ttk.Frame(self.root, padding=18)
        container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(container, style="Card.TFrame", padding=18)
        header.pack(fill=tk.X, pady=(0, 16))
        ttk.Label(
            header,
            text="Gelir ve giderlerinizi güvenli şekilde SQLite üzerinde yönetin.",
            style="Header.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            header,
            text="Filtreler, grafikler ve dışa aktarma seçenekleri ile modern masaüstü deneyimi.",
            style="Card.TLabel",
        ).pack(anchor="w", pady=(6, 0))

        metrics = ttk.Frame(container)
        metrics.pack(fill=tk.X, pady=(0, 16))
        self.metric_labels: dict[str, ttk.Label] = {}
        for key, title in (
            ("toplam_gelir", "Toplam Gelir"),
            ("toplam_gider", "Toplam Gider"),
            ("bakiye", "Bakiye"),
            ("kayit_sayisi", "Kayıt Sayısı"),
        ):
            card = ttk.Frame(metrics, style="Card.TFrame", padding=16)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))
            ttk.Label(card, text=title, style="MetricTitle.TLabel").pack(anchor="w")
            label = ttk.Label(card, text="0", style="MetricValue.TLabel")
            label.pack(anchor="w", pady=(8, 0))
            self.metric_labels[key] = label
        metrics.winfo_children()[-1].pack_configure(padx=(0, 0))

        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.transactions_tab = ttk.Frame(self.notebook, padding=12)
        self.chart_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.transactions_tab, text="İşlemler")
        self.notebook.add(self.chart_tab, text="Pasta Grafiği")

        self._build_transactions_tab()
        self._build_chart_tab()

        status_bar = ttk.Frame(self.root, style="Card.TFrame", padding=(12, 8))
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Label(status_bar, textvariable=self.status_var, style="Card.TLabel").pack(anchor="w")

    def _build_menu(self) -> None:
        """Create top menu."""
        menu = tk.Menu(self.root, bg=self.colors["panel"], fg=self.colors["text"], tearoff=0)
        dosya_menu = tk.Menu(menu, tearoff=0, bg=self.colors["panel"], fg=self.colors["text"])
        dosya_menu.add_command(label="Yeni Defter", command=self.yeni_defter)
        dosya_menu.add_command(label="CSV Dışa Aktar", command=self.disari_aktar_csv)
        dosya_menu.add_command(label="PDF Raporu Al", command=self.disari_aktar_pdf)
        dosya_menu.add_separator()
        dosya_menu.add_command(label="Çıkış", command=self.on_close)
        menu.add_cascade(label="Dosya", menu=dosya_menu)

        yardim_menu = tk.Menu(menu, tearoff=0, bg=self.colors["panel"], fg=self.colors["text"])
        yardim_menu.add_command(label="Hakkında", command=self.hakkinda)
        menu.add_cascade(label="Yardım", menu=yardim_menu)
        self.root.config(menu=menu)

    def _build_transactions_tab(self) -> None:
        """Create data entry form, filters and table widgets."""
        form_frame = ttk.LabelFrame(self.transactions_tab, text="Yeni Kayıt", padding=16)
        form_frame.pack(fill=tk.X, pady=(0, 14))

        row1 = ttk.Frame(form_frame)
        row1.pack(fill=tk.X, pady=(0, 10))
        row2 = ttk.Frame(form_frame)
        row2.pack(fill=tk.X)

        self._add_form_field(row1, "Tip", ttk.Combobox(
            row1,
            textvariable=self.tip_var,
            values=["gelir", "gider"],
            state="readonly",
            width=16,
        ))
        self._add_form_field(row1, "Tutar (₺)", ttk.Entry(row1, textvariable=self.tutar_var, width=18))
        self.kategori_combo = ttk.Combobox(
            row1,
            textvariable=self.kategori_var,
            values=DEFAULT_CATEGORIES,
            width=20,
        )
        self._add_form_field(row1, "Kategori", self.kategori_combo)

        self._add_form_field(row2, "Açıklama", ttk.Entry(row2, textvariable=self.aciklama_var, width=44))
        self._add_form_field(row2, "Tarih (YYYY-AA-GG)", ttk.Entry(row2, textvariable=self.tarih_var, width=18))

        actions = ttk.Frame(form_frame)
        actions.pack(anchor="e", pady=(14, 0))
        ttk.Button(actions, text="Kaydet", command=self.kayit_ekle).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(
            actions,
            text="Temizle",
            style="Secondary.TButton",
            command=self.form_temizle,
        ).pack(side=tk.LEFT)

        filter_frame = ttk.LabelFrame(self.transactions_tab, text="Filtreler", padding=16)
        filter_frame.pack(fill=tk.X, pady=(0, 14))

        self.tarih_filtre_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.tarih_filtre_var,
            values=DATE_FILTERS,
            state="readonly",
            width=14,
        )
        self.kategori_filtre_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.kategori_filtre_var,
            values=["Tümü"],
            state="readonly",
            width=20,
        )
        self._add_form_field(filter_frame, "Dönem", self.tarih_filtre_combo)
        self._add_form_field(filter_frame, "Kategori", self.kategori_filtre_combo)
        ttk.Button(
            filter_frame,
            text="Filtreyi Uygula",
            style="Secondary.TButton",
            command=self.refresh_all_views,
        ).pack(side=tk.LEFT, padx=6, pady=6)
        ttk.Button(
            filter_frame,
            text="Sıfırla",
            style="Secondary.TButton",
            command=self.reset_filters,
        ).pack(side=tk.LEFT, padx=6, pady=6)

        table_frame = ttk.LabelFrame(self.transactions_tab, text="İşlem Geçmişi", padding=12)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "tarih", "tip", "kategori", "tutar", "aciklama")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        headings = {
            "id": "ID",
            "tarih": "Tarih",
            "tip": "Tip",
            "kategori": "Kategori",
            "tutar": "Tutar (₺)",
            "aciklama": "Açıklama",
        }
        widths = {"id": 70, "tarih": 120, "tip": 120, "kategori": 160, "tutar": 140, "aciklama": 420}
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="center")
        self.tree.column("aciklama", anchor="w")

        scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        footer = ttk.Frame(table_frame)
        footer.grid(row=2, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(
            footer,
            text="Seçili Kaydı Sil",
            style="Danger.TButton",
            command=self.kayit_sil,
        ).pack(side=tk.LEFT)

    def _build_chart_tab(self) -> None:
        """Create matplotlib chart container."""
        frame = ttk.Frame(self.chart_tab, style="Card.TFrame", padding=12)
        frame.pack(fill=tk.BOTH, expand=True)
        self.figure = Figure(figsize=(6, 5), dpi=100, facecolor=self.colors["card"])
        self.chart_axis = self.figure.add_subplot(111)
        self.chart_canvas = FigureCanvasTkAgg(self.figure, master=frame)
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _add_form_field(self, parent: ttk.Widget, label_text: str, widget: ttk.Widget) -> None:
        """Render a label + widget group inline."""
        wrapper = ttk.Frame(parent)
        wrapper.pack(side=tk.LEFT, padx=6, pady=6)
        ttk.Label(wrapper, text=label_text).pack(anchor="w", pady=(0, 4))
        widget.pack(anchor="w")

    def validate_transaction_input(self) -> dict[str, object]:
        """Validate current form values and return normalized data."""
        tip = self.tip_var.get().strip().lower()
        if tip not in {"gelir", "gider"}:
            raise ValueError("Lütfen geçerli bir işlem tipi seçin.")

        try:
            tutar = float(self.tutar_var.get().replace(",", "."))
        except ValueError as exc:
            raise ValueError("Geçerli bir tutar giriniz.") from exc

        if tutar <= 0:
            raise ValueError("Tutar 0'dan büyük olmalıdır.")

        kategori = self.kategori_var.get().strip()
        if not kategori:
            raise ValueError("Lütfen bir kategori girin veya seçin.")

        tarih = self.tarih_var.get().strip()
        try:
            datetime.strptime(tarih, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Tarih biçimi YYYY-AA-GG olmalıdır.") from exc

        return {
            "tip": tip,
            "tutar": round(tutar, 2),
            "kategori": kategori,
            "aciklama": self.aciklama_var.get().strip(),
            "tarih": tarih,
        }

    def kayit_ekle(self) -> None:
        """Save a validated transaction and refresh views methodically."""
        try:
            payload = self.validate_transaction_input()
            self.db.add_transaction(payload)
        except ValueError as exc:
            messagebox.showerror("Doğrulama Hatası", str(exc))
            self.status_var.set(f"Hata: {exc}")
            return
        except Exception as exc:  # pragma: no cover - defensive UI error path
            messagebox.showerror("Beklenmeyen Hata", str(exc))
            self.status_var.set(f"Beklenmeyen hata: {exc}")
            return

        self.form_temizle()
        self.refresh_all_views()
        self.status_var.set("Kayıt başarıyla eklendi.")
        messagebox.showinfo("Başarılı", "Kayıt eklendi.")

    def kayit_sil(self) -> None:
        """Delete the selected transaction by its database id."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen silinecek kaydı seçin.")
            return

        item_id = selection[0]
        transaction_id = self.tree_index_map.get(item_id)
        if transaction_id is None:
            messagebox.showerror("Hata", "Seçili kayıt bulunamadı.")
            return

        if not messagebox.askyesno("Onay", "Seçili kaydı silmek istediğinize emin misiniz?"):
            return

        self.db.delete_transaction(transaction_id)
        self.refresh_all_views()
        self.status_var.set("Kayıt silindi.")
        messagebox.showinfo("Başarılı", "Kayıt silindi.")

    def form_temizle(self) -> None:
        """Reset form widgets to their default state."""
        self.tip_var.set("gelir")
        self.tutar_var.set("")
        self.kategori_var.set("")
        self.aciklama_var.set("")
        self.tarih_var.set(datetime.now().strftime("%Y-%m-%d"))

    def reset_filters(self) -> None:
        """Reset filter widgets and refresh the UI."""
        self.tarih_filtre_var.set("Tümü")
        self.kategori_filtre_var.set("Tümü")
        self.refresh_all_views()

    def refresh_all_views(self) -> None:
        """Refresh filters, table, metrics and chart in one safe sequence."""
        self._refresh_category_options()
        self.filtered_records = self.db.fetch_transactions(
            self.tarih_filtre_var.get(),
            self.kategori_filtre_var.get(),
        )
        self._refresh_table()
        self._refresh_summary()
        self._refresh_chart()

    def _refresh_category_options(self) -> None:
        """Update category lists for form and filter comboboxes."""
        categories = sorted(set(DEFAULT_CATEGORIES + self.db.get_categories()), key=str.lower)
        self.kategori_combo.configure(values=categories)
        filter_values = ["Tümü"] + categories
        self.kategori_filtre_combo.configure(values=filter_values)
        if self.kategori_filtre_var.get() not in filter_values:
            self.kategori_filtre_var.set("Tümü")

    def _refresh_table(self) -> None:
        """Render the filtered records inside the treeview."""
        self.tree.delete(*self.tree.get_children())
        self.tree_index_map.clear()
        for record in self.filtered_records:
            row_id = self.tree.insert(
                "",
                tk.END,
                values=(
                    record.id,
                    record.tarih,
                    "📈 Gelir" if record.tip == "gelir" else "📉 Gider",
                    record.kategori,
                    f"{record.tutar:,.2f}",
                    record.aciklama,
                ),
                tags=(record.tip,),
            )
            self.tree_index_map[row_id] = record.id
        self.tree.tag_configure("gelir", foreground="#86efac")
        self.tree.tag_configure("gider", foreground="#fca5a5")

    def _refresh_summary(self) -> None:
        """Update metric cards using current filter state."""
        summary = self.db.get_summary(
            self.tarih_filtre_var.get(),
            self.kategori_filtre_var.get(),
        )
        self.metric_labels["toplam_gelir"].configure(text=f"{summary['toplam_gelir']:,.2f} ₺")
        self.metric_labels["toplam_gider"].configure(text=f"{summary['toplam_gider']:,.2f} ₺")
        self.metric_labels["bakiye"].configure(text=f"{summary['bakiye']:,.2f} ₺")
        self.metric_labels["kayit_sayisi"].configure(text=str(int(summary["kayit_sayisi"])))

    def _refresh_chart(self) -> None:
        """Redraw the pie chart for filtered expense data."""
        data = self.db.get_expense_distribution(
            self.tarih_filtre_var.get(),
            self.kategori_filtre_var.get(),
        )
        self.chart_axis.clear()
        self.chart_axis.set_facecolor(self.colors["card"])
        self.figure.patch.set_facecolor(self.colors["card"])

        if data:
            labels = [item[0] for item in data]
            amounts = [item[1] for item in data]
            pie_colors = ["#3b82f6", "#14b8a6", "#f97316", "#a855f7", "#eab308", "#ef4444", "#8b5cf6"]
            self.chart_axis.pie(
                amounts,
                labels=labels,
                autopct="%1.1f%%",
                startangle=120,
                textprops={"color": "white", "fontsize": 10},
                colors=pie_colors[: len(amounts)],
            )
            self.chart_axis.set_title("Gider Dağılımı", color="white", fontsize=14)
        else:
            self.chart_axis.text(
                0.5,
                0.5,
                "Grafik için gider kaydı bulunmuyor.",
                ha="center",
                va="center",
                color="white",
                fontsize=12,
            )
            self.chart_axis.set_title("Gider Dağılımı", color="white", fontsize=14)
        self.chart_canvas.draw_idle()

    def export_records(self) -> list[dict[str, object]]:
        """Serialize currently filtered records for CSV/PDF exports."""
        return [asdict(record) for record in self.filtered_records]

    def disari_aktar_csv(self) -> None:
        """Export filtered records to a structured CSV file."""
        records = self.export_records()
        if not records:
            messagebox.showinfo("Bilgi", "Aktarılacak kayıt bulunamadı.")
            return

        path = filedialog.asksaveasfilename(
            title="CSV Dışa Aktar",
            defaultextension=".csv",
            filetypes=[("CSV Dosyası", "*.csv")],
        )
        if not path:
            return

        with open(path, "w", encoding="utf-8-sig", newline="") as csv_file:
            writer = csv.writer(csv_file, delimiter=";")
            writer.writerow(["ID", "Tarih", "Tip", "Kategori", "Tutar (₺)", "Açıklama"])
            for record in records:
                writer.writerow([
                    record["id"],
                    record["tarih"],
                    record["tip"],
                    record["kategori"],
                    f"{record['tutar']:.2f}",
                    record["aciklama"],
                ])
        self.status_var.set(f"CSV dışa aktarıldı: {path}")
        messagebox.showinfo("Başarılı", f"CSV dosyası oluşturuldu:\n{path}")

    def disari_aktar_pdf(self) -> None:
        """Export a PDF report using matplotlib's PDF backend."""
        records = self.export_records()
        if not records:
            messagebox.showinfo("Bilgi", "PDF için aktarılacak kayıt bulunamadı.")
            return

        path = filedialog.asksaveasfilename(
            title="PDF Raporu Kaydet",
            defaultextension=".pdf",
            filetypes=[("PDF Dosyası", "*.pdf")],
        )
        if not path:
            return

        summary = self.db.get_summary(
            self.tarih_filtre_var.get(),
            self.kategori_filtre_var.get(),
        )
        with PdfPages(path) as pdf:
            summary_fig = Figure(figsize=(8.27, 11.69), facecolor="white")
            ax = summary_fig.add_subplot(111)
            ax.axis("off")
            summary_lines = [
                APP_TITLE,
                "PDF Finans Raporu",
                f"Oluşturulma Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                f"Filtreler: Dönem={self.tarih_filtre_var.get()} | Kategori={self.kategori_filtre_var.get()}",
                "",
                f"Toplam Gelir: {summary['toplam_gelir']:,.2f} ₺",
                f"Toplam Gider: {summary['toplam_gider']:,.2f} ₺",
                f"Bakiye: {summary['bakiye']:,.2f} ₺",
                f"Kayıt Sayısı: {int(summary['kayit_sayisi'])}",
            ]
            ax.text(0.05, 0.95, "\n".join(summary_lines), va="top", fontsize=12)
            pdf.savefig(summary_fig)

            chart_fig = Figure(figsize=(8.27, 11.69), facecolor="white")
            chart_ax = chart_fig.add_subplot(111)
            distribution = self.db.get_expense_distribution(
                self.tarih_filtre_var.get(),
                self.kategori_filtre_var.get(),
            )
            if distribution:
                labels = [item[0] for item in distribution]
                amounts = [item[1] for item in distribution]
                chart_ax.pie(amounts, labels=labels, autopct="%1.1f%%", startangle=120)
                chart_ax.set_title("Gider Dağılımı")
            else:
                chart_ax.text(0.5, 0.5, "Gider dağılımı bulunamadı.", ha="center", va="center")
                chart_ax.axis("off")
            pdf.savefig(chart_fig)

            rows_per_page = 24
            for start_index in range(0, len(records), rows_per_page):
                page_records = records[start_index : start_index + rows_per_page]
                table_fig = Figure(figsize=(11.69, 8.27), facecolor="white")
                table_ax = table_fig.add_subplot(111)
                table_ax.axis("off")
                table_data = [
                    [
                        record["id"],
                        record["tarih"],
                        record["tip"],
                        record["kategori"],
                        f"{record['tutar']:.2f}",
                        record["aciklama"][:40],
                    ]
                    for record in page_records
                ]
                table = table_ax.table(
                    cellText=table_data,
                    colLabels=["ID", "Tarih", "Tip", "Kategori", "Tutar", "Açıklama"],
                    loc="center",
                    cellLoc="center",
                )
                table.auto_set_font_size(False)
                table.set_fontsize(8)
                table.scale(1, 1.4)
                pdf.savefig(table_fig)

        self.status_var.set(f"PDF raporu oluşturuldu: {path}")
        messagebox.showinfo("Başarılı", f"PDF raporu oluşturuldu:\n{path}")

    def yeni_defter(self) -> None:
        """Delete all transactions after confirmation."""
        if not messagebox.askyesno(
            "Onay",
            "Yeni defter oluşturulacak ve tüm kayıtlar silinecek. Devam etmek istiyor musunuz?",
        ):
            return

        self.db.reset_transactions()
        self.refresh_all_views()
        self.status_var.set("Yeni defter oluşturuldu.")
        messagebox.showinfo("Başarılı", "Tüm kayıtlar silindi ve yeni defter hazırlandı.")

    def hakkinda(self) -> None:
        """Show about dialog."""
        messagebox.showinfo(
            "Hakkında",
            "Muhasebe Takip Programı v2.0\n"
            "SQLite, ttk dark mode ve matplotlib ile modernize edildi.\n\n"
            "Özellikler:\n"
            "• SQLite veri tabanı\n"
            "• Kategori ve tarih filtreleri\n"
            "• Pasta grafiği\n"
            "• CSV ve PDF dışa aktarma",
        )

    def on_close(self) -> None:
        """Close database connection and destroy window."""
        self.db.close()
        self.root.destroy()


def main() -> None:
    """Application entry point."""
    root = tk.Tk()
    MuhasebeProgrami(root)
    root.mainloop()


if __name__ == "__main__":
    main()
