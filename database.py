"""SQLite database helper for Noura Accounting."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

DB_FILE = Path("noura_accounting.db")


class DatabaseManager:
    """Simple database wrapper around SQLite3."""

    def __init__(self, db_path: Path = DB_FILE) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._enable_foreign_keys()
        self._create_tables()
        self._migrate_schema()
        self._ensure_settings_row()

    def _enable_foreign_keys(self) -> None:
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def _create_tables(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT,
                tax_number TEXT,
                created_at DATETIME
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                unit_price REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0,
                unit TEXT,
                created_at DATETIME
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                invoice_date DATE,
                due_date DATE,
                total_amount REAL,
                status TEXT,
                created_at DATETIME,
                FOREIGN KEY(customer_id) REFERENCES customers(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                product_id INTEGER,
                description TEXT,
                quantity REAL,
                unit_price REAL,
                line_total REAL,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES products(id)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                company_name TEXT,
                company_phone TEXT,
                company_address TEXT,
                default_currency TEXT,
                theme TEXT,
                language TEXT
            )
            """
        )
        self.conn.commit()

    def _migrate_schema(self) -> None:
        """Handle small schema evolutions safely.

        The app might be running on an existing database. We keep migrations
        lightweight and additive. For larger changes, deleting the local DB and
        letting the app recreate it is also acceptable in early development
        (documented here for clarity).
        """

        cur = self.conn.execute("PRAGMA table_info(products)")
        columns = {row[1] for row in cur.fetchall()}
        if "stock" not in columns:
            self.conn.execute(
                "ALTER TABLE products ADD COLUMN stock INTEGER NOT NULL DEFAULT 0"
            )
            self.conn.commit()

    def _ensure_settings_row(self) -> None:
        """Guarantee a singleton settings row with defaults."""

        cur = self.conn.execute("SELECT COUNT(*) FROM settings WHERE id = 1")
        count = cur.fetchone()[0]
        if count == 0:
            self.conn.execute(
                """
                INSERT INTO settings (
                    id, company_name, company_phone, company_address, default_currency, theme, language
                )
                VALUES (1, 'Noura', '', '', 'USD', 'dark', 'en')
                """
            )
            self.conn.commit()

    # Customer operations
    def fetch_customers(self) -> List[sqlite3.Row]:
        cur = self.conn.execute(
            "SELECT id, name, email, phone, address, tax_number, created_at FROM customers ORDER BY id DESC"
        )
        return cur.fetchall()

    def add_customer(self, data: Dict[str, Any]) -> int:
        now = datetime.utcnow().isoformat()
        cur = self.conn.execute(
            """
            INSERT INTO customers (name, email, phone, address, tax_number, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("name"),
                data.get("email"),
                data.get("phone"),
                data.get("address"),
                data.get("tax_number"),
                now,
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_customer(self, customer_id: int, data: Dict[str, Any]) -> None:
        self.conn.execute(
            """
            UPDATE customers
            SET name=?, email=?, phone=?, address=?, tax_number=?
            WHERE id=?
            """,
            (
                data.get("name"),
                data.get("email"),
                data.get("phone"),
                data.get("address"),
                data.get("tax_number"),
                customer_id,
            ),
        )
        self.conn.commit()

    def delete_customer(self, customer_id: int) -> None:
        self.conn.execute("DELETE FROM customers WHERE id=?", (customer_id,))
        self.conn.commit()

    # Product operations
    def fetch_products(self) -> List[sqlite3.Row]:
        cur = self.conn.execute(
            """
            SELECT id, name, description, unit_price, stock, unit, created_at
            FROM products ORDER BY id DESC
            """
        )
        return cur.fetchall()

    def add_product(self, data: Dict[str, Any]) -> int:
        now = datetime.utcnow().isoformat()
        cur = self.conn.execute(
            """
            INSERT INTO products (name, description, unit_price, stock, unit, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("name"),
                data.get("description"),
                data.get("unit_price", 0.0),
                data.get("stock", 0),
                data.get("unit"),
                now,
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def update_product(self, product_id: int, data: Dict[str, Any]) -> None:
        self.conn.execute(
            """
            UPDATE products
            SET name=?, description=?, unit_price=?, stock=?, unit=?
            WHERE id=?
            """,
            (
                data.get("name"),
                data.get("description"),
                data.get("unit_price", 0.0),
                data.get("stock", 0),
                data.get("unit"),
                product_id,
            ),
        )
        self.conn.commit()

    def delete_product(self, product_id: int) -> None:
        self.conn.execute("DELETE FROM products WHERE id=?", (product_id,))
        self.conn.commit()

    # Invoice operations
    def add_invoice(self, invoice: Dict[str, Any], items: List[Dict[str, Any]]) -> int:
        now = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO invoices (invoice_number, customer_id, invoice_date, due_date, total_amount, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invoice.get("invoice_number"),
                invoice.get("customer_id"),
                invoice.get("invoice_date"),
                invoice.get("due_date"),
                invoice.get("total_amount", 0.0),
                invoice.get("status"),
                now,
            ),
        )
        invoice_id = cur.lastrowid
        for item in items:
            cur.execute(
                """
                INSERT INTO invoice_items (invoice_id, product_id, description, quantity, unit_price, line_total)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice_id,
                    item.get("product_id"),
                    item.get("description"),
                    item.get("quantity", 0.0),
                    item.get("unit_price", 0.0),
                    item.get("line_total", 0.0),
                ),
            )
        self.conn.commit()
        return invoice_id

    def update_invoice(self, invoice_id: int, invoice: Dict[str, Any], items: List[Dict[str, Any]]) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE invoices
            SET invoice_number=?, customer_id=?, invoice_date=?, due_date=?, total_amount=?, status=?
            WHERE id=?
            """,
            (
                invoice.get("invoice_number"),
                invoice.get("customer_id"),
                invoice.get("invoice_date"),
                invoice.get("due_date"),
                invoice.get("total_amount", 0.0),
                invoice.get("status"),
                invoice_id,
            ),
        )
        cur.execute("DELETE FROM invoice_items WHERE invoice_id=?", (invoice_id,))
        for item in items:
            cur.execute(
                """
                INSERT INTO invoice_items (invoice_id, product_id, description, quantity, unit_price, line_total)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    invoice_id,
                    item.get("product_id"),
                    item.get("description"),
                    item.get("quantity", 0.0),
                    item.get("unit_price", 0.0),
                    item.get("line_total", 0.0),
                ),
            )
        self.conn.commit()

    def delete_invoice(self, invoice_id: int) -> None:
        self.conn.execute("DELETE FROM invoices WHERE id=?", (invoice_id,))
        self.conn.commit()

    def fetch_invoices(self) -> List[sqlite3.Row]:
        cur = self.conn.execute(
            """
            SELECT i.id, i.invoice_number, i.invoice_date, i.due_date, i.total_amount, i.status,
                   c.name as customer_name
            FROM invoices i
            LEFT JOIN customers c ON c.id = i.customer_id
            ORDER BY i.id DESC
            """
        )
        return cur.fetchall()

    def get_invoice_with_items(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Return a full invoice payload with its items for printing/export."""

        cur = self.conn.execute(
            """
            SELECT i.id, i.invoice_number, i.invoice_date, i.due_date, i.total_amount, i.status,
                   c.name as customer_name, c.email as customer_email, c.address as customer_address
            FROM invoices i
            LEFT JOIN customers c ON c.id = i.customer_id
            WHERE i.id=?
            """,
            (invoice_id,),
        )
        invoice_row = cur.fetchone()
        if not invoice_row:
            return None

        items_cur = self.conn.execute(
            """
            SELECT p.name as product_name, ii.quantity, ii.unit_price, ii.line_total
            FROM invoice_items ii
            LEFT JOIN products p ON p.id = ii.product_id
            WHERE ii.invoice_id=?
            """,
            (invoice_id,),
        )
        return {
            "id": invoice_row["id"],
            "number": invoice_row["invoice_number"],
            "date": invoice_row["invoice_date"],
            "due_date": invoice_row["due_date"],
            "status": invoice_row["status"],
            "customer_name": invoice_row["customer_name"],
            "customer_email": invoice_row["customer_email"],
            "customer_address": invoice_row["customer_address"],
            "currency": None,
            "total": invoice_row["total_amount"],
            "items": [dict(row) for row in items_cur.fetchall()],
        }

    def get_invoice(self, invoice_id: int) -> Optional[sqlite3.Row]:
        cur = self.conn.execute(
            "SELECT id, invoice_number, customer_id, invoice_date, due_date, total_amount, status FROM invoices WHERE id=?",
            (invoice_id,),
        )
        return cur.fetchone()

    def fetch_invoice_items(self, invoice_id: int) -> List[sqlite3.Row]:
        cur = self.conn.execute(
            """
            SELECT id, invoice_id, product_id, description, quantity, unit_price, line_total
            FROM invoice_items
            WHERE invoice_id=?
            """,
            (invoice_id,),
        )
        return cur.fetchall()

    # Report helpers
    def totals_summary(self) -> Dict[str, Any]:
        summary: Dict[str, Any] = {}
        cur = self.conn.execute("SELECT COUNT(*) as total_customers FROM customers")
        summary.update(cur.fetchone())

        cur = self.conn.execute("SELECT COUNT(*) as total_invoices, SUM(total_amount) as total_revenue FROM invoices")
        summary.update(cur.fetchone())

        cur = self.conn.execute(
            "SELECT status, SUM(total_amount) as amount FROM invoices GROUP BY status"
        )
        summary["status_breakdown"] = {row[0] or "Unknown": row[1] or 0.0 for row in cur.fetchall()}
        return summary

    def get_invoice_status_totals(self) -> List[Tuple[str, float]]:
        """Return (status, total_amount) pairs grouped by invoice status."""

        cur = self.conn.execute(
            "SELECT status, SUM(total_amount) as total FROM invoices GROUP BY status"
        )
        return [(row[0] or "Unknown", row[1] or 0.0) for row in cur.fetchall()]

    # Settings helpers
    def get_settings(self) -> Dict[str, Any]:
        cur = self.conn.execute(
            """
            SELECT company_name, company_phone, company_address, default_currency, theme, language
            FROM settings WHERE id = 1
            """
        )
        row = cur.fetchone()
        if not row:
            # Should not happen because _ensure_settings_row enforces it, but
            # return safe defaults just in case.
            return {
                "company_name": "Noura",
                "company_phone": "",
                "company_address": "",
                "default_currency": "USD",
                "theme": "dark",
                "language": "en",
            }
        return dict(row)

    def save_settings(
        self,
        company_name: str,
        company_phone: str,
        company_address: str,
        default_currency: str,
        theme: str,
        language: str,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO settings (id, company_name, company_phone, company_address, default_currency, theme, language)
            VALUES (1, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                company_name=excluded.company_name,
                company_phone=excluded.company_phone,
                company_address=excluded.company_address,
                default_currency=excluded.default_currency,
                theme=excluded.theme,
                language=excluded.language
            """,
            (company_name, company_phone, company_address, default_currency, theme, language),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


def get_database(path: Path = DB_FILE) -> DatabaseManager:
    return DatabaseManager(path)
