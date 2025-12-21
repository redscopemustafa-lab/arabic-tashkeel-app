"""SQLite database helper for Noura Accounting."""

import sqlite3
import hashlib
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
                cost_price REAL NOT NULL DEFAULT 0,
                sale_price REAL NOT NULL DEFAULT 0,
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
                discount REAL DEFAULT 0,
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
                language TEXT,
                max_discount REAL DEFAULT 0
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                license_key TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
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
        if "cost_price" not in columns:
            self.conn.execute(
                "ALTER TABLE products ADD COLUMN cost_price REAL NOT NULL DEFAULT 0"
            )
            self.conn.execute(
                "ALTER TABLE products ADD COLUMN sale_price REAL NOT NULL DEFAULT 0"
            )
            # keep unit_price for backward compatibility but align values
            self.conn.execute("UPDATE products SET sale_price = unit_price WHERE sale_price = 0")
            self.conn.commit()

        cur = self.conn.execute("PRAGMA table_info(invoice_items)")
        item_columns = {row[1] for row in cur.fetchall()}
        if "discount" not in item_columns:
            self.conn.execute(
                "ALTER TABLE invoice_items ADD COLUMN discount REAL DEFAULT 0"
            )
            self.conn.commit()

        cur = self.conn.execute("PRAGMA table_info(settings)")
        settings_cols = {row[1] for row in cur.fetchall()}
        if "max_discount" not in settings_cols:
            self.conn.execute(
                "ALTER TABLE settings ADD COLUMN max_discount REAL DEFAULT 0"
            )
            self.conn.commit()

        # Ensure admin_users table has at least one default admin
        cur = self.conn.execute("SELECT COUNT(*) FROM admin_users")
        if cur.fetchone()[0] == 0:
            # Default admin credentials: admin / admin / DEMO-KEY (should be changed in production)
            default_hash = hashlib.sha256("admin".encode()).hexdigest()
            self.conn.execute(
                "INSERT INTO admin_users (username, password_hash, license_key, is_active) VALUES (?, ?, ?, 1)",
                ("admin", default_hash, "DEMO-KEY"),
            )
            self.conn.commit()

    # ------------------------------------------------------------------
    # Stock helpers
    # ------------------------------------------------------------------
    def _validate_stock_levels(self, items: List[Dict[str, Any]]) -> None:
        """Ensure there is enough stock for each product.

        Raises a ValueError with a readable message if any product would drop
        below zero. Custom line items (product_id is None) are ignored.
        """

        for item in items:
            product_id = item.get("product_id")
            quantity = float(item.get("quantity") or 0)
            if product_id is None:
                continue
            cur = self.conn.execute(
                "SELECT stock, name FROM products WHERE id=?", (product_id,)
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("Product not found for invoice item")
            if (row["stock"] or 0) < quantity:
                raise ValueError(
                    f"Insufficient stock for {row['name']} (have {row['stock']}, need {quantity})."
                )

    def _apply_stock_changes(self, items: List[Dict[str, Any]], multiplier: int) -> None:
        """Increment or decrement stock for a list of items.

        *multiplier* should be 1 to add back quantities (e.g. deleting invoices)
        or -1 to subtract (e.g. creating invoices). Custom items are skipped.
        """

        for item in items:
            product_id = item.get("product_id")
            quantity = float(item.get("quantity") or 0)
            if product_id is None:
                continue
            self.conn.execute(
                "UPDATE products SET stock = stock + ? WHERE id=?",
                (multiplier * quantity, product_id),
            )

    def get_invoice_item_quantities(self, invoice_id: int) -> List[Dict[str, Any]]:
        """Return product_id/quantity pairs for an invoice (for stock handling)."""

        cur = self.conn.execute(
            "SELECT product_id, quantity FROM invoice_items WHERE invoice_id=?",
            (invoice_id,),
        )
        return [dict(row) for row in cur.fetchall()]

    def _ensure_settings_row(self) -> None:
        """Guarantee a singleton settings row with defaults."""

        cur = self.conn.execute("SELECT COUNT(*) FROM settings WHERE id = 1")
        count = cur.fetchone()[0]
        if count == 0:
            self.conn.execute(
                """
                INSERT INTO settings (
                    id, company_name, company_phone, company_address, default_currency, theme, language, max_discount
                )
                VALUES (1, 'Noura', '', '', 'USD', 'dark', 'en', 0)
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
            SELECT id, name, description, unit_price, cost_price, sale_price, stock, unit, created_at
            FROM products ORDER BY id DESC
            """
        )
        return cur.fetchall()

    def add_product(self, data: Dict[str, Any]) -> int:
        now = datetime.utcnow().isoformat()
        cur = self.conn.execute(
            """
            INSERT INTO products (name, description, unit_price, cost_price, sale_price, stock, unit, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("name"),
                data.get("description"),
                data.get("unit_price", data.get("sale_price", 0.0)),
                data.get("cost_price", 0.0),
                data.get("sale_price", data.get("unit_price", 0.0)),
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
            SET name=?, description=?, unit_price=?, cost_price=?, sale_price=?, stock=?, unit=?
            WHERE id=?
            """,
            (
                data.get("name"),
                data.get("description"),
                data.get("unit_price", data.get("sale_price", 0.0)),
                data.get("cost_price", 0.0),
                data.get("sale_price", data.get("unit_price", 0.0)),
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
        try:
            # Validate stock before writing anything
            self._validate_stock_levels(items)

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
                    INSERT INTO invoice_items (invoice_id, product_id, description, quantity, unit_price, discount, line_total)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        invoice_id,
                        item.get("product_id"),
                        item.get("description"),
                        item.get("quantity", 0.0),
                        item.get("unit_price", 0.0),
                        item.get("discount", 0.0),
                        item.get("line_total", 0.0),
                    ),
                )
            # Subtract stock now that the invoice rows exist
            self._apply_stock_changes(items, multiplier=-1)
            self.conn.commit()
            return invoice_id
        except Exception:
            self.conn.rollback()
            raise

    def update_invoice(self, invoice_id: int, invoice: Dict[str, Any], items: List[Dict[str, Any]]) -> None:
        cur = self.conn.cursor()
        try:
            previous_items = self.get_invoice_item_quantities(invoice_id)
            # Restore stock from old items first
            self._apply_stock_changes(previous_items, multiplier=1)

            # Validate against the replenished stock before subtracting again
            self._validate_stock_levels(items)

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
                    INSERT INTO invoice_items (invoice_id, product_id, description, quantity, unit_price, discount, line_total)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        invoice_id,
                        item.get("product_id"),
                        item.get("description"),
                        item.get("quantity", 0.0),
                        item.get("unit_price", 0.0),
                        item.get("discount", 0.0),
                        item.get("line_total", 0.0),
                    ),
                )
            # Apply stock decrease for new items
            self._apply_stock_changes(items, multiplier=-1)
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def delete_invoice(self, invoice_id: int) -> None:
        try:
            # Restore stock for all items before deleting
            items = self.get_invoice_item_quantities(invoice_id)
            self._apply_stock_changes(items, multiplier=1)
            self.conn.execute("DELETE FROM invoices WHERE id=?", (invoice_id,))
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

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
            SELECT p.name as product_name, ii.description, ii.quantity, ii.unit_price, ii.discount, ii.line_total
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
            SELECT id, invoice_id, product_id, description, quantity, unit_price, discount, line_total
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

    def daily_income(self, days: int = 30) -> List[Tuple[str, float, float]]:
        """Return list of (date, gross, net) for recent days."""
        cur = self.conn.execute(
            """
            SELECT i.invoice_date as d,
                   SUM(ii.quantity * ii.unit_price) as gross,
                   SUM(ii.quantity * IFNULL(p.cost_price,0)) as cost,
                   SUM(ii.quantity * ii.unit_price * (ii.discount/100.0)) as discount_amt
            FROM invoice_items ii
            JOIN invoices i ON i.id = ii.invoice_id
            LEFT JOIN products p ON p.id = ii.product_id
            WHERE i.invoice_date >= date('now', ?)
            GROUP BY i.invoice_date
            ORDER BY i.invoice_date DESC
            LIMIT ?
            """,
            (f"-{days} day", days),
        )
        rows = cur.fetchall()
        return [(
            row[0],
            row[1] or 0.0,
            (row[1] or 0.0) - (row[2] or 0.0) - (row[3] or 0.0),
        ) for row in rows]

    def monthly_income(self, months: int = 12) -> List[Tuple[str, float, float]]:
        cur = self.conn.execute(
            """
            SELECT strftime('%Y-%m', i.invoice_date) as m,
                   SUM(ii.quantity * ii.unit_price) as gross,
                   SUM(ii.quantity * IFNULL(p.cost_price,0)) as cost,
                   SUM(ii.quantity * ii.unit_price * (ii.discount/100.0)) as discount_amt
            FROM invoice_items ii
            JOIN invoices i ON i.id = ii.invoice_id
            LEFT JOIN products p ON p.id = ii.product_id
            GROUP BY m
            ORDER BY m DESC
            LIMIT ?
            """,
            (months,),
        )
        rows = cur.fetchall()
        return [(
            row[0],
            row[1] or 0.0,
            (row[1] or 0.0) - (row[2] or 0.0) - (row[3] or 0.0),
        ) for row in rows]

    def yearly_income(self, years: int = 5) -> List[Tuple[str, float, float]]:
        cur = self.conn.execute(
            """
            SELECT strftime('%Y', i.invoice_date) as y,
                   SUM(ii.quantity * ii.unit_price) as gross,
                   SUM(ii.quantity * IFNULL(p.cost_price,0)) as cost,
                   SUM(ii.quantity * ii.unit_price * (ii.discount/100.0)) as discount_amt
            FROM invoice_items ii
            JOIN invoices i ON i.id = ii.invoice_id
            LEFT JOIN products p ON p.id = ii.product_id
            GROUP BY y
            ORDER BY y DESC
            LIMIT ?
            """,
            (years,),
        )
        rows = cur.fetchall()
        return [(
            row[0],
            row[1] or 0.0,
            (row[1] or 0.0) - (row[2] or 0.0) - (row[3] or 0.0),
        ) for row in rows]

    def product_sales_summary(self) -> List[Dict[str, Any]]:
        cur = self.conn.execute(
            """
            SELECT p.name, SUM(ii.quantity) as qty, SUM(ii.line_total) as revenue,
                   SUM(ii.quantity * ii.unit_price * (ii.discount/100.0)) as discount_amt
            FROM invoice_items ii
            LEFT JOIN products p ON p.id = ii.product_id
            GROUP BY p.name
            ORDER BY revenue DESC
            """
        )
        return [dict(row) for row in cur.fetchall()]

    def authenticate_admin(self, username: str, password: str, license_key: str) -> bool:
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        cur = self.conn.execute(
            """
            SELECT id FROM admin_users
            WHERE username=? AND password_hash=? AND license_key=? AND is_active=1
            """,
            (username, pwd_hash, license_key),
        )
        return cur.fetchone() is not None

    # Settings helpers
    def get_settings(self) -> Dict[str, Any]:
        cur = self.conn.execute(
            """
            SELECT company_name, company_phone, company_address, default_currency, theme, language, max_discount
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
                "max_discount": 0,
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
        max_discount: float,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO settings (id, company_name, company_phone, company_address, default_currency, theme, language, max_discount)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                company_name=excluded.company_name,
                company_phone=excluded.company_phone,
                company_address=excluded.company_address,
                default_currency=excluded.default_currency,
                theme=excluded.theme,
                language=excluded.language,
                max_discount=excluded.max_discount
            """,
            (company_name, company_phone, company_address, default_currency, theme, language, max_discount),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


def get_database(path: Path = DB_FILE) -> DatabaseManager:
    return DatabaseManager(path)
