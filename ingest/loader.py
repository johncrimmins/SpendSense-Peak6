"""CSV -> SQLite loader for SpendSense synthetic datasets.

This script consumes the deterministic CSV files that `ingest/generator.py`
creates and normalizes them into a relational SQLite database that downstream
modules (feature engineering, persona classifier, APIs) can query.

Usage:
    python ingest/loader.py --input-dir data/raw --database spendsense.db
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, Iterator

REQUIRED_FILES = ("users.csv", "accounts.csv", "transactions.csv", "liabilities.csv")


def parse_bool(value: str | bool) -> int:
    if isinstance(value, bool):
        return int(value)
    normalized = str(value).strip().lower()
    return int(normalized in {"1", "true", "yes"})


def parse_float(value: str | float) -> float:
    if value in (None, "", "NULL"):
        return 0.0
    return float(value)


def parse_int(value: str | int) -> int:
    if value in (None, "", "NULL"):
        return 0
    return int(value)


def parse_optional(value: str) -> str | None:
    trimmed = value.strip()
    return trimmed or None


@dataclass
class LoaderConfig:
    input_dir: Path
    database: Path
    force: bool


class DataLoader:
    def __init__(self, config: LoaderConfig) -> None:
        self.config = config

    def run(self) -> Dict[str, int]:
        self._validate_input_dir()
        if self.config.force and self.config.database.exists():
            self.config.database.unlink()

        with sqlite3.connect(self.config.database) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")
            self._create_tables(conn)
            counts = {
                "users": self._load_users(conn),
                "accounts": self._load_accounts(conn),
                "transactions": self._load_transactions(conn),
                "liabilities": self._load_liabilities(conn),
            }
            self._record_audit(conn, counts)
            conn.commit()
        return counts

    def _validate_input_dir(self) -> None:
        if not self.config.input_dir.exists():
            raise FileNotFoundError(
                f"Input directory {self.config.input_dir} does not exist. "
                "Run ingest/generator.py first."
            )
        missing = [
            name
            for name in REQUIRED_FILES
            if not (self.config.input_dir / name).exists()
        ]
        if missing:
            raise FileNotFoundError(
                f"Missing files in {self.config.input_dir}: {', '.join(missing)}"
            )

    @staticmethod
    def _create_tables(conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                persona_hint TEXT NOT NULL,
                persona_priority INTEGER NOT NULL,
                consent_granted INTEGER NOT NULL,
                consent_ts TEXT NOT NULL,
                city TEXT,
                region TEXT
            );

            CREATE TABLE IF NOT EXISTS accounts (
                account_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                subtype TEXT NOT NULL,
                mask TEXT,
                available_balance REAL,
                current_balance REAL,
                credit_limit REAL,
                iso_currency_code TEXT,
                holder_category TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                account_id TEXT NOT NULL,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                merchant_name TEXT,
                category_primary TEXT,
                category_detailed TEXT,
                payment_channel TEXT,
                is_subscription INTEGER NOT NULL,
                pending INTEGER NOT NULL,
                currency_code TEXT,
                recurring_group_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (account_id) REFERENCES accounts(account_id)
            );

            CREATE TABLE IF NOT EXISTS liabilities (
                account_id TEXT PRIMARY KEY,
                apr_type TEXT,
                apr_percentage REAL,
                minimum_payment_amount REAL,
                last_payment_amount REAL,
                last_statement_balance REAL,
                is_overdue INTEGER,
                next_payment_due_date TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts(account_id)
            );

            CREATE TABLE IF NOT EXISTS ingest_audit (
                run_id TEXT PRIMARY KEY,
                input_dir TEXT NOT NULL,
                created_at TEXT NOT NULL,
                user_rows INTEGER,
                account_rows INTEGER,
                transaction_rows INTEGER,
                liability_rows INTEGER
            );

            CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts(user_id);
            CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
            CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id);
            """
        )

    def _iter_csv(self, filename: str) -> Iterator[Dict[str, str]]:
        path = self.config.input_dir / filename
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                yield {key: (value or "").strip() for key, value in row.items()}

    def _load_users(self, conn: sqlite3.Connection) -> int:
        rows = [
            (
                record["user_id"],
                record["full_name"],
                record["email"],
                record["persona_hint"],
                parse_int(record["persona_priority"]),
                parse_bool(record["consent_granted"]),
                record["consent_ts"],
                record["city"],
                record["region"],
            )
            for record in self._iter_csv("users.csv")
        ]
        conn.executemany(
            """
            INSERT OR REPLACE INTO users (
                user_id,
                full_name,
                email,
                persona_hint,
                persona_priority,
                consent_granted,
                consent_ts,
                city,
                region
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            rows,
        )
        return len(rows)

    def _load_accounts(self, conn: sqlite3.Connection) -> int:
        rows = [
            (
                record["account_id"],
                record["user_id"],
                record["name"],
                record["type"],
                record["subtype"],
                record["mask"],
                parse_float(record["available_balance"]),
                parse_float(record["current_balance"]),
                parse_float(record["limit"]),
                record["iso_currency_code"],
                record["holder_category"],
            )
            for record in self._iter_csv("accounts.csv")
        ]
        conn.executemany(
            """
            INSERT OR REPLACE INTO accounts (
                account_id,
                user_id,
                name,
                type,
                subtype,
                mask,
                available_balance,
                current_balance,
                credit_limit,
                iso_currency_code,
                holder_category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            rows,
        )
        return len(rows)

    def _load_transactions(self, conn: sqlite3.Connection) -> int:
        rows = [
            (
                record["transaction_id"],
                record["user_id"],
                record["account_id"],
                record["date"],
                parse_float(record["amount"]),
                record["merchant_name"],
                record["category_primary"],
                record["category_detailed"],
                record["payment_channel"],
                parse_bool(record["is_subscription"]),
                parse_bool(record["pending"]),
                record["currency_code"],
                parse_optional(record.get("recurring_group_id", "")),
            )
            for record in self._iter_csv("transactions.csv")
        ]
        conn.executemany(
            """
            INSERT OR REPLACE INTO transactions (
                transaction_id,
                user_id,
                account_id,
                date,
                amount,
                merchant_name,
                category_primary,
                category_detailed,
                payment_channel,
                is_subscription,
                pending,
                currency_code,
                recurring_group_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            rows,
        )
        return len(rows)

    def _load_liabilities(self, conn: sqlite3.Connection) -> int:
        rows = [
            (
                record["account_id"],
                record["apr_type"],
                parse_float(record["apr_percentage"]),
                parse_float(record["minimum_payment_amount"]),
                parse_float(record["last_payment_amount"]),
                parse_float(record["last_statement_balance"]),
                parse_bool(record["is_overdue"]),
                record["next_payment_due_date"],
            )
            for record in self._iter_csv("liabilities.csv")
        ]
        conn.executemany(
            """
            INSERT OR REPLACE INTO liabilities (
                account_id,
                apr_type,
                apr_percentage,
                minimum_payment_amount,
                last_payment_amount,
                last_statement_balance,
                is_overdue,
                next_payment_due_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            rows,
        )
        return len(rows)

    def _record_audit(self, conn: sqlite3.Connection, counts: Dict[str, int]) -> None:
        run_id = datetime.now(UTC).isoformat(timespec="seconds")
        conn.execute(
            """
            INSERT INTO ingest_audit (
                run_id,
                input_dir,
                created_at,
                user_rows,
                account_rows,
                transaction_rows,
                liability_rows
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                run_id,
                str(self.config.input_dir.absolute()),
                run_id,
                counts["users"],
                counts["accounts"],
                counts["transactions"],
                counts["liabilities"],
            ),
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load SpendSense CSVs into SQLite.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory containing generator CSV outputs.",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("spendsense.db"),
        help="Destination SQLite database path.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the existing database file if it already exists.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = LoaderConfig(input_dir=args.input_dir, database=args.database, force=args.force)
    loader = DataLoader(config)
    counts = loader.run()
    print(
        "Loaded dataset into "
        f"{config.database} "
        f"(users={counts['users']}, accounts={counts['accounts']}, "
        f"transactions={counts['transactions']}, liabilities={counts['liabilities']})"
    )


if __name__ == "__main__":
    main()
