"""Tiny translation helper for common UI strings.

The app only needs lightweight translations for core navigation and the most
visible buttons. This module keeps a central dictionary for those strings.
"""

from typing import Dict


TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "dashboard": "Dashboard",
        "customers": "Customers",
        "products": "Products",
        "invoices": "Invoices",
        "reports": "Reports",
        "settings": "Settings",
        "admin_panel": "Admin Panel",
        "add": "Add",
        "edit": "Edit",
        "delete": "Delete",
        "new_invoice": "New Invoice",
        "edit_invoice": "Edit Invoice",
        "delete_invoice": "Delete Invoice",
        "print_export": "Print / Export PDF",
        "save_settings": "Save Settings",
        "company_name": "Company Name",
        "company_phone": "Company Phone",
        "company_address": "Company Address",
        "default_currency": "Default Currency",
        "theme": "Theme",
        "language": "Language",
        "stock": "Stock",
    },
    "tr": {
        "dashboard": "Gösterge Paneli",
        "customers": "Müşteriler",
        "products": "Ürünler",
        "invoices": "Faturalar",
        "reports": "Raporlar",
        "settings": "Ayarlar",
        "admin_panel": "Yönetim Paneli",
        "add": "Ekle",
        "edit": "Düzenle",
        "delete": "Sil",
        "new_invoice": "Yeni Fatura",
        "edit_invoice": "Faturayı Düzenle",
        "delete_invoice": "Faturayı Sil",
        "print_export": "Yazdır / PDF Dışa Aktar",
        "save_settings": "Ayarları Kaydet",
        "company_name": "Şirket Adı",
        "company_phone": "Şirket Telefonu",
        "company_address": "Şirket Adresi",
        "default_currency": "Varsayılan Para Birimi",
        "theme": "Tema",
        "language": "Dil",
        "stock": "Stok",
    },
    "id": {
        "dashboard": "Dasbor",
        "customers": "Pelanggan",
        "products": "Produk",
        "invoices": "Faktur",
        "reports": "Laporan",
        "settings": "Pengaturan",
        "admin_panel": "Panel Admin",
        "add": "Tambah",
        "edit": "Edit",
        "delete": "Hapus",
        "new_invoice": "Faktur Baru",
        "edit_invoice": "Edit Faktur",
        "delete_invoice": "Hapus Faktur",
        "print_export": "Cetak / Ekspor PDF",
        "save_settings": "Simpan Pengaturan",
        "company_name": "Nama Perusahaan",
        "company_phone": "Telepon Perusahaan",
        "company_address": "Alamat Perusahaan",
        "default_currency": "Mata Uang Default",
        "theme": "Tema",
        "language": "Bahasa",
        "stock": "Stok",
    },
    "ar": {
        "dashboard": "لوحة التحكم",
        "customers": "العملاء",
        "products": "المنتجات",
        "invoices": "الفواتير",
        "reports": "التقارير",
        "settings": "الإعدادات",
        "admin_panel": "لوحة الإدارة",
        "add": "إضافة",
        "edit": "تعديل",
        "delete": "حذف",
        "new_invoice": "فاتورة جديدة",
        "edit_invoice": "تعديل الفاتورة",
        "delete_invoice": "حذف الفاتورة",
        "print_export": "طباعة / تصدير PDF",
        "save_settings": "حفظ الإعدادات",
        "company_name": "اسم الشركة",
        "company_phone": "هاتف الشركة",
        "company_address": "عنوان الشركة",
        "default_currency": "العملة الافتراضية",
        "theme": "السمة",
        "language": "اللغة",
        "stock": "المخزون",
    },
}


def translate(language: str, key: str) -> str:
    """Return translation for *key* using *language* with English fallback."""

    lang_dict = TRANSLATIONS.get(language, TRANSLATIONS["en"])
    return lang_dict.get(key, TRANSLATIONS["en"].get(key, key))

