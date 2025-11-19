"""SQLite loader for the SpendSense synthetic dataset."""
from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CSV_DIR = ROOT_DIR / "data" / "synthetic"
DEFAULT_DB_PATH = ROOT_DIR / "spendsense.db"

USER_COLUMNS = (
    "user_id",
    "full_name",
    "email",
    "persona_hint",
    "monthly_income",
    "income_volatility_pct",
    "subscription_ratio",
    "credit_utilization_target",
    "cash_buffer_months",
    "savings_rate",
)

ACCOUNT_COLUMNS = (
    "account_id",
    "user_id",
    "account_type",
    "current_balance",
    "credit_limit",
    "iso_currency_code",
)

TRANSACTION_COLUMNS = (
    "transaction_id",
    "user_id",
    "account_id",
    "merchant_name",
    "amount",
    "date",
    "category",
    "type",
    "is_subscription",
)

SCHEMA_SQL = (
    "PRAGMA foreign_keys = ON;",
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        full_name TEXT,
        email TEXT,
        persona_hint TEXT,
        monthly_income REAL,
        income_volatility_pct REAL,
        subscription_ratio REAL,
        credit_utilization_target REAL,
        cash_buffer_months REAL,
        savings_rate REAL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS accounts (
        account_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        account_type TEXT NOT NULL,
        current_balance REAL,
        credit_limit REAL,
        iso_currency_code TEXT,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        account_id TEXT NOT NULL,
        merchant_name TEXT,
        amount REAL,
        date TEXT,
        category TEXT,
        type TEXT,
        is_subscription INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(user_id),
        FOREIGN KEY(account_id) REFERENCES accounts(account_id)
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, date);",
)


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def normalize_float(value: str) -> float | None:
    if value == "" or value is None:
        return None
    return float(value)


def normalize_int(value: str) -> int:
    return int(value)


def normalize_users(rows: List[Dict[str, str]]) -> List[Tuple]:
    normalized: List[Tuple] = []
    for row in rows:
        normalized.append(
            (
                row["user_id"],
                row["full_name"],
                row["email"],
                row["persona_hint"],
                float(row["monthly_income"]),
                float(row["income_volatility_pct"]),
                float(row["subscription_ratio"]),
                float(row["credit_utilization_target"]),
                float(row["cash_buffer_months"]),
                float(row["savings_rate"]),
            )
        )
    return normalized


def normalize_accounts(rows: List[Dict[str, str]]) -> List[Tuple]:
    normalized: List[Tuple] = []
    for row in rows:
        normalized.append(
            (
                row["account_id"],
                row["user_id"],
                row["account_type"],
                float(row["current_balance"]),
                normalize_float(row["credit_limit"]),
                row["iso_currency_code"],
            )
        )
    return normalized


def normalize_transactions(rows: List[Dict[str, str]]) -> List[Tuple]:
    normalized: List[Tuple] = []
    for row in rows:
        normalized.append(
            (
                row["transaction_id"],
                row["user_id"],
                row["account_id"],
                row["merchant_name"],
                float(row["amount"]),
                row["date"],
                row["category"],
                row["type"],
                1 if str(row["is_subscription"]).lower() in {"1", "true", "yes"} else 0,
            )
        )
    return normalized


def prepare_schema(conn: sqlite3.Connection, reset: bool) -> None:
    cur = conn.cursor()
    if reset:
        cur.execute("DROP TABLE IF EXISTS transactions;")
        cur.execute("DROP TABLE IF EXISTS accounts;")
        cur.execute("DROP TABLE IF EXISTS users;")
    for statement in SCHEMA_SQL:
        cur.execute(statement)
    conn.commit()


def bulk_insert(
    conn: sqlite3.Connection,
    table: str,
    columns: Sequence[str],
    rows: Iterable[Tuple],
) -> None:
    placeholders = ", ".join(["?"] * len(columns))
    column_clause = ", ".join(columns)
    sql = f"INSERT OR REPLACE INTO {table} ({column_clause}) VALUES ({placeholders})"
    conn.executemany(sql, rows)


def load_database(csv_dir: Path, db_path: Path, reset: bool = False) -> None:
    if not csv_dir.exists():
        raise FileNotFoundError(f"CSV directory not found: {csv_dir}")

    user_rows = normalize_users(read_csv(csv_dir / "users.csv"))
    account_rows = normalize_accounts(read_csv(csv_dir / "accounts.csv"))
    transaction_rows = normalize_transactions(read_csv(csv_dir / "transactions.csv"))

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        prepare_schema(conn, reset)
        bulk_insert(conn, "users", USER_COLUMNS, user_rows)
        bulk_insert(conn, "accounts", ACCOUNT_COLUMNS, account_rows)
        bulk_insert(conn, "transactions", TRANSACTION_COLUMNS, transaction_rows)
        conn.commit()
    finally:
        conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load synthetic CSVs into spendsense.db")
    parser.add_argument("--csv-dir", type=Path, default=DEFAULT_CSV_DIR, help="Directory containing generated CSVs")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="SQLite database path")
    parser.add_argument("--reset", action="store_true", help="Drop existing tables before loading")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_database(args.csv_dir, args.db, args.reset)
    print(f"Loaded dataset from {args.csv_dir} into {args.db}")


if __name__ == "__main__":
    main()
