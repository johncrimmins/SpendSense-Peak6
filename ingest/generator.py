"""
SpendSense synthetic data generator.

Creates deterministic, persona-aware dummy data covering:
  * Users (with persona signals)
  * Accounts (checking, savings, credit)
  * Transactions (Plaid-style fields)

Usage:
    python -m ingest.generator --users 80 --output data/raw
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from faker import Faker

ISO_CURRENCY = "USD"
MONTHS_OF_HISTORY = 6
OUTPUT_DEFAULT = Path("data/raw")

# Merchant templates (merchant name, Plaid-style category, base amount USD)
SUBSCRIPTION_MERCHANTS: Sequence[Tuple[str, str, float]] = [
    ("Netflix", "Entertainment > Video Streaming", 16.0),
    ("Spotify", "Entertainment > Music and Audio", 11.0),
    ("Adobe Creative Cloud", "Shops > Digital Purchases", 55.0),
    ("iCloud Storage", "Utilities > Internet", 12.0),
    ("Peloton", "Sports and Fitness > Gym", 45.0),
    ("Calm App", "Health and Wellness > Mental Health", 70.0),
    ("Amazon Subscribe & Save", "Shops > Retail", 28.0),
]

EXPENSE_MERCHANTS: Sequence[Tuple[str, str, float]] = [
    ("Whole Foods", "Food and Drink > Groceries", 140.0),
    ("Sweetgreen", "Food and Drink > Restaurants", 28.0),
    ("Delta Airlines", "Travel > Airlines", 320.0),
    ("Shell Gas", "Travel > Gas Stations", 65.0),
    ("Equinox", "Sports and Fitness > Gym", 210.0),
    ("Target", "Shops > Retail", 85.0),
    ("Wayfair", "Home > Furniture", 260.0),
    ("Lyft", "Travel > Ride Share", 25.0),
    ("Comcast", "Utilities > Cable", 130.0),
    ("Soho House", "Entertainment > Nightlife", 180.0),
]

INCOME_SOURCES = [
    "Acme Corp Payroll",
    "Upwork Payouts",
    "Stripe Atlas Distributions",
    "AngelList Advisory",
    "Monarch Labs Consulting",
]


@dataclass(frozen=True)
class PersonaConfig:
    label: str
    monthly_income: Tuple[float, float]
    spend_ratio: Tuple[float, float]
    subscription_ratio: Tuple[float, float]
    cash_buffer_months: Tuple[float, float]
    savings_rate: Tuple[float, float]
    credit_utilization: Tuple[float, float]
    credit_limit: Tuple[float, float]
    income_volatility: float
    min_subscriptions: int
    max_subscriptions: int


PERSONA_CONFIGS: Sequence[PersonaConfig] = [
    PersonaConfig(
        label="Debt Fighter",
        monthly_income=(3200, 6400),
        spend_ratio=(1.05, 1.25),
        subscription_ratio=(0.05, 0.1),
        cash_buffer_months=(0.5, 1.5),
        savings_rate=(0.00, 0.05),
        credit_utilization=(0.55, 0.95),
        credit_limit=(4000, 12000),
        income_volatility=0.12,
        min_subscriptions=2,
        max_subscriptions=4,
    ),
    PersonaConfig(
        label="Gig Worker",
        monthly_income=(3800, 7000),
        spend_ratio=(0.9, 1.05),
        subscription_ratio=(0.04, 0.08),
        cash_buffer_months=(1.0, 2.0),
        savings_rate=(0.02, 0.08),
        credit_utilization=(0.25, 0.5),
        credit_limit=(6000, 14000),
        income_volatility=0.38,
        min_subscriptions=1,
        max_subscriptions=3,
    ),
    PersonaConfig(
        label="Auto-Payer",
        monthly_income=(5000, 9000),
        spend_ratio=(0.85, 1.0),
        subscription_ratio=(0.12, 0.22),
        cash_buffer_months=(1.5, 3.0),
        savings_rate=(0.05, 0.12),
        credit_utilization=(0.2, 0.45),
        credit_limit=(7000, 18000),
        income_volatility=0.08,
        min_subscriptions=4,
        max_subscriptions=7,
    ),
    PersonaConfig(
        label="Wealth Compounder",
        monthly_income=(12000, 22000),
        spend_ratio=(0.65, 0.85),
        subscription_ratio=(0.06, 0.12),
        cash_buffer_months=(3.5, 7.0),
        savings_rate=(0.03, 0.08),
        credit_utilization=(0.05, 0.25),
        credit_limit=(20000, 40000),
        income_volatility=0.07,
        min_subscriptions=3,
        max_subscriptions=5,
    ),
    PersonaConfig(
        label="Optimizer",
        monthly_income=(6500, 11000),
        spend_ratio=(0.6, 0.8),
        subscription_ratio=(0.04, 0.09),
        cash_buffer_months=(2.5, 4.0),
        savings_rate=(0.12, 0.2),
        credit_utilization=(0.05, 0.15),
        credit_limit=(10000, 20000),
        income_volatility=0.05,
        min_subscriptions=2,
        max_subscriptions=4,
    ),
]


def cycle_persona(index: int) -> PersonaConfig:
    return PERSONA_CONFIGS[index % len(PERSONA_CONFIGS)]


def pick_subscription_merchants(rng: random.Random, count: int) -> Sequence[Tuple[str, str, float]]:
    max_count = min(count, len(SUBSCRIPTION_MERCHANTS))
    return rng.sample(SUBSCRIPTION_MERCHANTS, max_count)


def build_subscription_transactions(
    user_id: str,
    account_id: str,
    base_total: float,
    merchants: Sequence[Tuple[str, str, float]],
    month_idx: int,
    rng: random.Random,
) -> List[Dict[str, object]]:
    """Scale merchant base charges to match base_total for the month."""
    if not merchants:
        return []

    total_base = sum(m[2] for m in merchants)
    scale = base_total / total_base if total_base else 1.0
    txns = []
    month_date = month_anchor(month_idx, rng)
    counter = 0
    for merchant, category, amount in merchants:
        counter += 1
        scaled = round(amount * scale, 2)
        txns.append(
            {
                "transaction_id": f"{user_id}_SUB_{month_idx}_{counter:02d}",
                "user_id": user_id,
                "account_id": account_id,
                "merchant_name": merchant,
                "amount": -scaled,
                "date": month_date.isoformat(),
                "category": category,
                "transaction_type": "debit",
                "is_subscription": True,
                "is_income": False,
            }
        )
    return txns


def month_anchor(month_idx: int, rng: random.Random) -> date:
    today = date.today()
    days_ago = (MONTHS_OF_HISTORY - month_idx) * 30
    offset = rng.randint(0, 24)
    return today - timedelta(days=days_ago - offset)


def write_csv(path: Path, rows: Iterable[Dict[str, object]], headers: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def generate_user_dataset(
    num_users: int,
    output_dir: Path,
    seed: int = 42,
) -> None:
    rng = random.Random(seed)
    fake = Faker()
    fake.seed_instance(seed)

    users: List[Dict[str, object]] = []
    accounts: List[Dict[str, object]] = []
    transactions: List[Dict[str, object]] = []

    for idx in range(num_users):
        persona = cycle_persona(idx)
        user_id = f"USR{idx + 1:04d}"
        full_name = fake.name()

        monthly_income = rng.uniform(*persona.monthly_income)
        spend_ratio = rng.uniform(*persona.spend_ratio)
        monthly_spend = monthly_income * spend_ratio

        subscription_ratio = rng.uniform(*persona.subscription_ratio)
        subscription_spend = monthly_spend * subscription_ratio
        other_spend = max(50.0, monthly_spend - subscription_spend)

        savings_rate = rng.uniform(*persona.savings_rate)
        credit_utilization = rng.uniform(*persona.credit_utilization)

        credit_limit = rng.uniform(*persona.credit_limit)
        outstanding_cc = credit_limit * credit_utilization

        buffer_months = rng.uniform(*persona.cash_buffer_months)
        checking_balance = monthly_spend * buffer_months * 0.6
        savings_balance = monthly_spend * buffer_months * 0.4

        subscription_count = rng.randint(persona.min_subscriptions, persona.max_subscriptions)
        subs = pick_subscription_merchants(rng, subscription_count)

        account_defs = [
            ("CHK", "checking", round(checking_balance, 2)),
            ("SVG", "savings", round(savings_balance, 2)),
            ("CRD", "credit", round(outstanding_cc, 2)),
        ]

        for suffix, acct_type, balance in account_defs:
            account_id = f"{user_id}_{suffix}"
            accounts.append(
                {
                    "account_id": account_id,
                    "user_id": user_id,
                    "account_type": acct_type,
                    "account_name": f"{full_name.split()[0]}'s {acct_type.title()}",
                    "current_balance": round(balance, 2),
                    "iso_currency_code": ISO_CURRENCY,
                }
            )

        txn_counter = 0
        for month_idx in range(1, MONTHS_OF_HISTORY + 1):
            # Income events
            income_events = max(1, 1 if persona.label != "Gig Worker" else rng.randint(2, 4))
            month_income = monthly_income
            if persona.income_volatility > 0:
                jitter = rng.uniform(-persona.income_volatility, persona.income_volatility)
                month_income *= 1 + jitter
            income_split = distribute_amount(month_income, income_events, rng)
            for event_amt in income_split:
                txn_counter += 1
                transactions.append(
                    {
                        "transaction_id": f"{user_id}_INC_{month_idx}_{txn_counter:03d}",
                        "user_id": user_id,
                        "account_id": f"{user_id}_CHK",
                        "merchant_name": rng.choice(INCOME_SOURCES),
                        "amount": round(event_amt, 2),
                        "date": month_anchor(month_idx, rng).isoformat(),
                        "category": "Income > Payroll",
                        "transaction_type": "credit",
                        "is_subscription": False,
                        "is_income": True,
                    }
                )

            # Subscription debits (mostly on credit)
            subs_total = subscription_spend
            subs_txns = build_subscription_transactions(
                user_id=user_id,
                account_id=f"{user_id}_CRD",
                base_total=subs_total,
                merchants=subs,
                month_idx=month_idx,
                rng=rng,
            )
            txn_counter += len(subs_txns)
            transactions.extend(subs_txns)

            # Other expenses
            expense_txns = build_expense_transactions(
                user_id=user_id,
                month_idx=month_idx,
                target_total=other_spend,
                rng=rng,
            )
            txn_counter += len(expense_txns)
            transactions.extend(expense_txns)

            # Interest charge for debt fighters
            if persona.label == "Debt Fighter":
                interest = round(outstanding_cc * 0.02, 2)
                txn_counter += 1
                transactions.append(
                    {
                        "transaction_id": f"{user_id}_INT_{month_idx}_{txn_counter:03d}",
                        "user_id": user_id,
                        "account_id": f"{user_id}_CRD",
                        "merchant_name": "Card APR Charge",
                        "amount": -interest,
                        "date": month_anchor(month_idx, rng).isoformat(),
                        "category": "Finance > Interest",
                        "transaction_type": "debit",
                        "is_subscription": False,
                        "is_income": False,
                    }
                )

        users.append(
            {
                "user_id": user_id,
                "full_name": full_name,
                "primary_persona": persona.label,
                "monthly_income": round(monthly_income, 2),
                "monthly_spend": round(monthly_spend, 2),
                "subscription_ratio": round(subscription_ratio, 3),
                "subscription_count": len(subs),
                "savings_rate": round(savings_rate, 3),
                "credit_utilization": round(credit_utilization, 3),
                "cash_buffer_months": round(buffer_months, 2),
                "credit_limit": round(credit_limit, 2),
            }
        )

    write_csv(
        output_dir / "users.csv",
        users,
        headers=[
            "user_id",
            "full_name",
            "primary_persona",
            "monthly_income",
            "monthly_spend",
            "subscription_ratio",
            "subscription_count",
            "savings_rate",
            "credit_utilization",
            "cash_buffer_months",
            "credit_limit",
        ],
    )
    write_csv(
        output_dir / "accounts.csv",
        accounts,
        headers=[
            "account_id",
            "user_id",
            "account_type",
            "account_name",
            "current_balance",
            "iso_currency_code",
        ],
    )
    write_csv(
        output_dir / "transactions.csv",
        transactions,
        headers=[
            "transaction_id",
            "user_id",
            "account_id",
            "merchant_name",
            "amount",
            "date",
            "category",
            "transaction_type",
            "is_subscription",
            "is_income",
        ],
    )
    write_json(
        output_dir / "manifest.json",
        {
            "generated_on": date.today().isoformat(),
            "num_users": num_users,
            "months_of_history": MONTHS_OF_HISTORY,
            "seed": seed,
            "personas": [config.label for config in PERSONA_CONFIGS],
        },
    )


def build_expense_transactions(
    user_id: str,
    month_idx: int,
    target_total: float,
    rng: random.Random,
) -> List[Dict[str, object]]:
    sample_size = rng.randint(5, 10)
    picked = rng.choices(EXPENSE_MERCHANTS, k=sample_size)
    total_base = sum(m[2] for m in picked)
    scale = target_total / total_base if total_base else 1.0
    txns: List[Dict[str, object]] = []
    for idx, (merchant, category, amount) in enumerate(picked, start=1):
        scaled = round(amount * scale * rng.uniform(0.85, 1.15), 2)
        account_id = f"{user_id}_{'CRD' if rng.random() < 0.6 else 'CHK'}"
        txns.append(
            {
                "transaction_id": f"{user_id}_EXP_{month_idx}_{idx:03d}",
                "user_id": user_id,
                "account_id": account_id,
                "merchant_name": merchant,
                "amount": -scaled,
                "date": month_anchor(month_idx, rng).isoformat(),
                "category": category,
                "transaction_type": "debit",
                "is_subscription": False,
                "is_income": False,
            }
        )
    return txns


def distribute_amount(total: float, parts: int, rng: random.Random) -> List[float]:
    allocations = [rng.random() for _ in range(parts)]
    allocations_sum = sum(allocations)
    if allocations_sum == 0:
        allocations = [1.0 for _ in range(parts)]
        allocations_sum = float(parts)
    normalized = [a / allocations_sum for a in allocations]
    return [round(total * share, 2) for share in normalized]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic SpendSense data.")
    parser.add_argument(
        "--users",
        type=int,
        default=75,
        help="Number of synthetic users to generate (must be between 50 and 100).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed for deterministic generation.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DEFAULT,
        help="Directory where CSV/JSON outputs will be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not 50 <= args.users <= 100:
        raise ValueError("Specification requires between 50 and 100 users.")
    generate_user_dataset(
        num_users=args.users,
        output_dir=args.output,
        seed=args.seed,
    )
    print(f"✅ Generated dataset for {args.users} users in {args.output}")


if __name__ == "__main__":
    main()
