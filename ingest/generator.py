"""Synthetic data generator for SpendSense.

Creates deterministic Plaid-style CSVs for users, accounts, and transactions while
covering all five primary personas so downstream logic has realistic signals.
"""
from __future__ import annotations

import argparse
import csv
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Sequence
from uuid import NAMESPACE_DNS, uuid5

from faker import Faker

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT_DIR / "data" / "synthetic"
SEED = 42
CURRENCY = "USD"
MONTH_DAYS = 30

faker = Faker()


@dataclass(frozen=True)
class PersonaBlueprint:
    name: str
    weight: int
    monthly_income: float
    income_volatility: float  # pct of income (0-1)
    monthly_spend: float
    subscription_ratio: float  # pct of spend
    credit_utilization: float  # 0-1
    cash_buffer_months: float
    savings_rate: float  # 0-1
    recurring_merchants: int
    avg_pay_gap_days: int


PERSONA_BLUEPRINTS: Sequence[PersonaBlueprint] = (
    PersonaBlueprint(
        name="Debt Fighter",
        weight=3,
        monthly_income=6200,
        income_volatility=0.08,
        monthly_spend=6000,
        subscription_ratio=0.06,
        credit_utilization=0.72,
        cash_buffer_months=0.6,
        savings_rate=0.01,
        recurring_merchants=2,
        avg_pay_gap_days=14,
    ),
    PersonaBlueprint(
        name="Gig Worker",
        weight=2,
        monthly_income=5200,
        income_volatility=0.38,
        monthly_spend=4700,
        subscription_ratio=0.08,
        credit_utilization=0.42,
        cash_buffer_months=1.2,
        savings_rate=0.05,
        recurring_merchants=2,
        avg_pay_gap_days=26,
    ),
    PersonaBlueprint(
        name="Auto-Payer",
        weight=2,
        monthly_income=6800,
        income_volatility=0.12,
        monthly_spend=6400,
        subscription_ratio=0.2,
        credit_utilization=0.36,
        cash_buffer_months=1.5,
        savings_rate=0.04,
        recurring_merchants=4,
        avg_pay_gap_days=14,
    ),
    PersonaBlueprint(
        name="Wealth Compounder",
        weight=2,
        monthly_income=11500,
        income_volatility=0.1,
        monthly_spend=9800,
        subscription_ratio=0.12,
        credit_utilization=0.21,
        cash_buffer_months=4.0,
        savings_rate=0.05,
        recurring_merchants=3,
        avg_pay_gap_days=14,
    ),
    PersonaBlueprint(
        name="Optimizer",
        weight=2,
        monthly_income=7200,
        income_volatility=0.06,
        monthly_spend=5600,
        subscription_ratio=0.09,
        credit_utilization=0.08,
        cash_buffer_months=2.5,
        savings_rate=0.18,
        recurring_merchants=3,
        avg_pay_gap_days=14,
    ),
)

SUBSCRIPTION_MERCHANTS = (
    ("Netflix", "Digital Subscriptions"),
    ("Spotify", "Digital Subscriptions"),
    ("Peloton", "Sporting Goods"),
    ("Apple iCloud", "Internet Services"),
    ("Calm App", "Health & Wellness"),
    ("Adobe", "Software"),
)
EVERYDAY_MERCHANTS = (
    ("Whole Foods", "Groceries"),
    ("Shell", "Gas Stations"),
    ("Blue Bottle Coffee", "Cafes"),
    ("Sweetgreen", "Restaurants"),
    ("Lyft", "Transportation"),
    ("Lululemon", "Retail"),
    ("Target", "Retail"),
    ("Trader Joe's", "Groceries"),
    ("Home Depot", "Home Improvement"),
)


def seed_everything(seed: int = SEED) -> None:
    random.seed(seed)
    Faker.seed(seed)
    faker.seed_instance(seed)


def roster(num_users: int) -> List[PersonaBlueprint]:
    weights = [bp.weight for bp in PERSONA_BLUEPRINTS]
    pool = list(PERSONA_BLUEPRINTS)
    total_weight = sum(weights)
    choices: List[PersonaBlueprint] = []
    idx = 0
    while len(choices) < num_users:
        blueprint = pool[idx % len(pool)]
        repetitions = max(1, math.ceil(num_users * (blueprint.weight / total_weight)))
        for _ in range(repetitions):
            choices.append(blueprint)
            if len(choices) == num_users:
                break
        idx += 1
    return choices


def make_account_id(user_id: str, suffix: str) -> str:
    return str(uuid5(NAMESPACE_DNS, f"{user_id}-{suffix}"))


def generate_users(num_users: int) -> List[Dict[str, str]]:
    users: List[Dict[str, str]] = []
    for idx, blueprint in enumerate(roster(num_users), start=1):
        profile = faker.simple_profile()
        user_id = f"USR{idx:04d}"
        users.append(
            {
                "user_id": user_id,
                "full_name": profile["name"],
                "email": profile["mail"],
                "persona_hint": blueprint.name,
                "monthly_income": round(blueprint.monthly_income, 2),
                "income_volatility_pct": round(blueprint.income_volatility, 3),
                "subscription_ratio": round(blueprint.subscription_ratio, 3),
                "credit_utilization_target": round(blueprint.credit_utilization, 3),
                "cash_buffer_months": round(blueprint.cash_buffer_months, 2),
                "savings_rate": round(blueprint.savings_rate, 3),
            }
        )
    return users


def generate_accounts(users: Sequence[Dict[str, str]]) -> List[Dict[str, str]]:
    accounts: List[Dict[str, str]] = []
    for user in users:
        buffer_months = float(user["cash_buffer_months"])
        monthly_spend = float(user["monthly_income"]) * (1 - float(user["savings_rate"]))
        checking_balance = monthly_spend * buffer_months
        savings_balance = monthly_spend * (buffer_months * 0.6)
        credit_limit = 20000 if monthly_spend > 8000 else 12000
        credit_balance = credit_limit * float(user["credit_utilization_target"])

        accounts.extend(
            [
                {
                    "account_id": make_account_id(user["user_id"], "checking"),
                    "user_id": user["user_id"],
                    "account_type": "checking",
                    "current_balance": round(checking_balance, 2),
                    "credit_limit": "",
                    "iso_currency_code": CURRENCY,
                },
                {
                    "account_id": make_account_id(user["user_id"], "savings"),
                    "user_id": user["user_id"],
                    "account_type": "savings",
                    "current_balance": round(savings_balance, 2),
                    "credit_limit": "",
                    "iso_currency_code": CURRENCY,
                },
                {
                    "account_id": make_account_id(user["user_id"], "credit"),
                    "user_id": user["user_id"],
                    "account_type": "credit",
                    "current_balance": round(credit_balance, 2),
                    "credit_limit": str(credit_limit),
                    "iso_currency_code": CURRENCY,
                },
            ]
        )
    return accounts


def _monthly_dates(months: int) -> List[int]:
    base = list(range(0, months * MONTH_DAYS, MONTH_DAYS))
    return base


def _subscription_events(
    blueprint: PersonaBlueprint, user_id: str, checking_id: str, period_start: date, month_idx: int
) -> List[Dict[str, object]]:
    events: List[Dict[str, object]] = []
    merchants = random.sample(SUBSCRIPTION_MERCHANTS, blueprint.recurring_merchants)
    monthly_subscription_total = blueprint.monthly_spend * blueprint.subscription_ratio
    per_charge = max(9.99, monthly_subscription_total / len(merchants))
    for i, (merchant, category) in enumerate(merchants):
        charge_date = period_start + timedelta(days=5 + (i * 3))
        events.append(
            {
                "user_id": user_id,
                "account_id": checking_id,
                "amount": round(-per_charge, 2),
                "date": charge_date,
                "merchant_name": merchant,
                "category": category,
                "type": "debit",
                "is_subscription": True,
            }
        )
    return events


def _income_events(
    blueprint: PersonaBlueprint, user_id: str, checking_id: str, period_start: date
) -> List[Dict[str, object]]:
    events: List[Dict[str, object]] = []
    for paycheck_idx in range(2):
        delta_days = paycheck_idx * blueprint.avg_pay_gap_days
        pay_date = period_start + timedelta(days=delta_days)
        # For gig workers, randomly skip a paycheck to enforce volatility.
        if blueprint.name == "Gig Worker" and paycheck_idx == 1 and random.random() < 0.35:
            continue
        paycheck = random.gauss(blueprint.monthly_income / 2, blueprint.monthly_income * blueprint.income_volatility / 2)
        events.append(
            {
                "user_id": user_id,
                "account_id": checking_id,
                "amount": round(paycheck, 2),
                "date": pay_date,
                "merchant_name": faker.company(),
                "category": "Income",
                "type": "credit",
                "is_subscription": False,
            }
        )
    return events


def _discretionary_events(
    blueprint: PersonaBlueprint, user_id: str, checking_id: str, period_start: date
) -> List[Dict[str, object]]:
    events: List[Dict[str, object]] = []
    base_spend = blueprint.monthly_spend * (1 - blueprint.subscription_ratio)
    num_events = 6 + random.randint(0, 6)
    avg_amount = base_spend / num_events
    merchants = random.choices(EVERYDAY_MERCHANTS, k=num_events)
    for offset, (merchant, category) in enumerate(merchants):
        spend = random.gauss(avg_amount, avg_amount * 0.3)
        tx_date = period_start + timedelta(days=8 + offset * 3)
        events.append(
            {
                "user_id": user_id,
                "account_id": checking_id,
                "amount": round(-abs(spend), 2),
                "date": tx_date,
                "merchant_name": merchant,
                "category": category,
                "type": "debit",
                "is_subscription": False,
            }
        )
    return events


def generate_transactions(
    users: Sequence[Dict[str, str]],
    accounts: Sequence[Dict[str, str]],
    months: int = 6,
) -> List[Dict[str, object]]:
    start_date = date.today() - timedelta(days=months * MONTH_DAYS)
    transactions: List[Dict[str, object]] = []
    account_by_user: Dict[str, Dict[str, str]] = defaultdict(dict)
    for acct in accounts:
        account_by_user[acct["user_id"]][acct["account_type"]] = acct["account_id"]
    transaction_counter = 0

    for user in users:
        blueprint = next(bp for bp in PERSONA_BLUEPRINTS if bp.name == user["persona_hint"])
        checking_id = account_by_user[user["user_id"]]["checking"]
        credit_id = account_by_user[user["user_id"]]["credit"]

        for month_idx, days_offset in enumerate(_monthly_dates(months)):
            period_start = start_date + timedelta(days=days_offset)
            period_events: List[Dict[str, object]] = []
            period_events.extend(_income_events(blueprint, user["user_id"], checking_id, period_start))
            period_events.extend(_subscription_events(blueprint, user["user_id"], checking_id, period_start, month_idx))
            period_events.extend(_discretionary_events(blueprint, user["user_id"], checking_id, period_start))

            # Credit card usage for Debt Fighters / Optimizers etc.
            if blueprint.credit_utilization > 0.1:
                swipe_amount = random.uniform(150, 1200)
                tx_date = period_start + timedelta(days=18)
                period_events.append(
                    {
                        "user_id": user["user_id"],
                        "account_id": credit_id,
                        "amount": round(-swipe_amount, 2),
                        "date": tx_date,
                        "merchant_name": random.choice(EVERYDAY_MERCHANTS)[0],
                        "category": "Credit Card",
                        "type": "debit",
                        "is_subscription": False,
                    }
                )

            for event in period_events:
                transaction_counter += 1
                transactions.append(
                    {
                        "transaction_id": f"TXN{transaction_counter:06d}",
                        "user_id": event["user_id"],
                        "account_id": event["account_id"],
                        "merchant_name": event["merchant_name"],
                        "amount": event["amount"],
                        "date": event["date"].isoformat(),
                        "category": event["category"],
                        "type": event["type"],
                        "is_subscription": event["is_subscription"],
                    }
                )
    return transactions


def _write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def generate_dataset(num_users: int, months: int, output_dir: Path) -> Dict[str, Path]:
    if not (50 <= num_users <= 100):
        raise ValueError("num_users must be between 50 and 100 to satisfy PRD volume goals")
    seed_everything(SEED)
    users = generate_users(num_users)
    accounts = generate_accounts(users)
    transactions = generate_transactions(users, accounts, months)

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "users": output_dir / "users.csv",
        "accounts": output_dir / "accounts.csv",
        "transactions": output_dir / "transactions.csv",
    }
    _write_csv(paths["users"], users, users[0].keys())
    _write_csv(paths["accounts"], accounts, accounts[0].keys())
    _write_csv(paths["transactions"], transactions, transactions[0].keys())
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate deterministic SpendSense synthetic dataset")
    parser.add_argument("--num-users", type=int, default=75, help="Number of synthetic users (50-100)")
    parser.add_argument("--months", type=int, default=6, help="Months of history to generate")
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output directory for generated CSV files",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = generate_dataset(args.num_users, args.months, args.out)
    print(
        "Generated synthetic dataset:",
        ", ".join(f"{name}={path}" for name, path in paths.items()),
    )


if __name__ == "__main__":
    main()
