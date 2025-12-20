"""SQLite database helper for Noura Accounting."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

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
            "SELECT id, name, description, unit_price, unit, created_at FROM products ORDER BY id DESC"
        )
        return cur.fetchall()

    def add_product(self, data: Dict[str, Any]) -> int:
        now = datetime.utcnow().isoformat()
        cur = self.conn.execute(
            """
            INSERT INTO products (name, description, unit_price, unit, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data.get("name"),
                data.get("description"),
                data.get("unit_price", 0.0),
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
            SET name=?, description=?, unit_price=?, unit=?
            WHERE id=?
            """,
            (
                data.get("name"),
                data.get("description"),
                data.get("unit_price", 0.0),
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

    def close(self) -> None:
        self.conn.close()


def get_database(path: Path = DB_FILE) -> DatabaseManager:
    return DatabaseManager(path)
