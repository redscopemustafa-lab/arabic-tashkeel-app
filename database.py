"""SQLite veri katmanı for the desktop accounting tracker."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DB_FILE = Path("muhasebe.db")


@dataclass(frozen=True)
class TransactionRecord:
    """Typed representation of a transaction row."""

    id: int
    tip: str
    tutar: float
    kategori: str
    aciklama: str
    tarih: str
    olusturulma: str


class DatabaseManager:
    """Manage SQLite connection and transaction queries."""

    def __init__(self, db_path: Path = DB_FILE) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        """Create application tables if they do not exist yet."""
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tip TEXT NOT NULL CHECK(tip IN ('gelir', 'gider')),
                tutar REAL NOT NULL CHECK(tutar > 0),
                kategori TEXT NOT NULL,
                aciklama TEXT NOT NULL DEFAULT '',
                tarih TEXT NOT NULL,
                olusturulma TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def add_transaction(self, data: Dict[str, Any]) -> int:
        """Insert a new transaction and return its row id."""
        cursor = self.conn.execute(
            """
            INSERT INTO transactions (tip, tutar, kategori, aciklama, tarih)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data["tip"],
                float(data["tutar"]),
                data["kategori"],
                data.get("aciklama", "").strip(),
                data["tarih"],
            ),
        )
        self.conn.commit()
        return int(cursor.lastrowid)

    def delete_transaction(self, transaction_id: int) -> None:
        """Delete a single transaction by id."""
        self.conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        self.conn.commit()

    def reset_transactions(self) -> None:
        """Delete all transactions."""
        self.conn.execute("DELETE FROM transactions")
        self.conn.commit()

    def fetch_transactions(
        self,
        date_filter: str = "Tümü",
        category_filter: str = "Tümü",
    ) -> List[TransactionRecord]:
        """Return filtered transactions ordered from newest to oldest."""
        where_clauses: List[str] = []
        params: List[Any] = []
        today_iso = date.today().isoformat()
        month_prefix = today_iso[:7]

        if date_filter == "Bugün":
            where_clauses.append("tarih = ?")
            params.append(today_iso)
        elif date_filter == "Bu Ay":
            where_clauses.append("substr(tarih, 1, 7) = ?")
            params.append(month_prefix)

        if category_filter and category_filter != "Tümü":
            where_clauses.append("kategori = ?")
            params.append(category_filter)

        query = """
            SELECT id, tip, tutar, kategori, aciklama, tarih, olusturulma
            FROM transactions
        """
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        query += " ORDER BY tarih DESC, id DESC"

        rows = self.conn.execute(query, params).fetchall()
        return [TransactionRecord(**dict(row)) for row in rows]

    def get_summary(
        self,
        date_filter: str = "Tümü",
        category_filter: str = "Tümü",
    ) -> Dict[str, float]:
        """Compute totals based on current filters."""
        records = self.fetch_transactions(date_filter, category_filter)
        toplam_gelir = sum(item.tutar for item in records if item.tip == "gelir")
        toplam_gider = sum(item.tutar for item in records if item.tip == "gider")
        return {
            "toplam_gelir": toplam_gelir,
            "toplam_gider": toplam_gider,
            "bakiye": toplam_gelir - toplam_gider,
            "kayit_sayisi": float(len(records)),
        }

    def get_categories(self) -> List[str]:
        """Return distinct categories in alphabetical order."""
        rows = self.conn.execute(
            "SELECT DISTINCT kategori FROM transactions ORDER BY kategori COLLATE NOCASE"
        ).fetchall()
        return [row[0] for row in rows]

    def get_expense_distribution(
        self,
        date_filter: str = "Tümü",
        category_filter: str = "Tümü",
    ) -> List[Tuple[str, float]]:
        """Return expense totals grouped by category for pie chart usage."""
        records = self.fetch_transactions(date_filter, category_filter)
        totals: Dict[str, float] = {}
        for item in records:
            if item.tip != "gider":
                continue
            totals[item.kategori] = totals.get(item.kategori, 0.0) + item.tutar
        return sorted(totals.items(), key=lambda pair: pair[1], reverse=True)

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()


def get_database(db_path: Optional[Path] = None) -> DatabaseManager:
    """Factory helper for consistency with the app entry point."""
    if db_path is None:
        return DatabaseManager(DB_FILE)
    return DatabaseManager(Path(db_path))
