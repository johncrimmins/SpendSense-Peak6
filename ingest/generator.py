"""Synthetic Plaid-style data generator for SpendSense.

This module creates deterministic CSVs for users, accounts, transactions, and
credit liabilities so downstream pipelines can rely on reproducible fixtures.

Usage:
    python ingest/generator.py --users 80 --seed 123

Outputs (relative to project root by default):
    data/raw/users.csv
    data/raw/accounts.csv
    data/raw/transactions.csv
    data/raw/liabilities.csv
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from faker import Faker


DEFAULT_USER_COUNT = 75
MIN_USERS = 50
MAX_USERS = 100
DEFAULT_HORIZON_DAYS = 120
DEFAULT_SEED = 42
USD = "USD"

USER_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "spendsense-users")
ACCOUNT_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "spendsense-accounts")
TRANSACTION_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "spendsense-transactions")


@dataclass(frozen=True)
class PersonaTemplate:
    name: str
    priority: int
    income_range: Tuple[int, int]
    savings_rate: Tuple[float, float]
    buffer_months: Tuple[float, float]
    credit_utilization: Tuple[float, float]
    card_spend_bias: float
    subscription_merchants: Tuple[int, int]
    subscription_share: Tuple[float, float]
    income_variance: float
    pay_gap_days: Tuple[int, int]
    variable_income: bool = False
    force_interest: bool = False
    allow_overdue: bool = False
    ensure_positive_savings: bool = False


@dataclass(frozen=True)
class ExpenseCategory:
    name: str
    primary: str
    detailed: str
    min_amount: float
    max_amount: float
    merchants: Tuple[str, ...]


@dataclass(frozen=True)
class SubscriptionProduct:
    name: str
    primary: str
    detailed: str
    base_amount: float
    cadence_days: int = 30


@dataclass
class UserRecord:
    user_id: str
    full_name: str
    email: str
    persona_hint: str
    persona_priority: int
    consent_granted: bool
    consent_ts: str
    city: str
    region: str


@dataclass
class AccountRecord:
    account_id: str
    user_id: str
    name: str
    type: str
    subtype: str
    mask: str
    available_balance: float
    current_balance: float
    limit: float
    iso_currency_code: str
    holder_category: str


@dataclass
class TransactionRecord:
    transaction_id: str
    user_id: str
    account_id: str
    date: date
    amount: float
    merchant_name: str
    category_primary: str
    category_detailed: str
    payment_channel: str
    is_subscription: bool
    pending: bool
    currency_code: str
    recurring_group_id: str | None


@dataclass
class LiabilityRecord:
    account_id: str
    apr_type: str
    apr_percentage: float
    minimum_payment_amount: float
    last_payment_amount: float
    last_statement_balance: float
    is_overdue: bool
    next_payment_due_date: date


EXPENSE_CATEGORIES: Tuple[ExpenseCategory, ...] = (
    ExpenseCategory(
        "Groceries",
        "FOOD_AND_DRINK",
        "GROCERIES",
        25,
        140,
        ("Whole Foods", "Trader Joe's", "Sprouts Market", "Fresh Market"),
    ),
    ExpenseCategory(
        "Dining",
        "FOOD_AND_DRINK",
        "RESTAURANTS",
        12,
        85,
        ("Sweetgreen", "Chipotle", "Shake Shack", "Local Bistro", "Blue Bottle Coffee"),
    ),
    ExpenseCategory(
        "Transportation",
        "TRANSPORTATION",
        "RIDESHARE",
        18,
        60,
        ("Uber", "Lyft", "City Transit", "Shell Fuel"),
    ),
    ExpenseCategory(
        "Utilities",
        "BILLS_AND_UTILITIES",
        "CELL_PHONE",
        45,
        140,
        ("Verizon Wireless", "AT&T Fiber", "Comcast", "T-Mobile"),
    ),
    ExpenseCategory(
        "Health",
        "HEALTHCARE",
        "PHARMACIES",
        30,
        120,
        ("CVS", "Walgreens", "One Medical", "City Dental"),
    ),
    ExpenseCategory(
        "Lifestyle",
        "SHOPPING",
        "GENERAL_MERCHANDISE",
        20,
        200,
        ("Amazon", "Apple Store", "REI", "Warby Parker"),
    ),
    ExpenseCategory(
        "Travel",
        "TRAVEL",
        "AIR_TRAVEL",
        80,
        350,
        ("Delta Airlines", "United Airlines", "Marriott", "Airbnb"),
    ),
)

SUBSCRIPTION_PRODUCTS: Tuple[SubscriptionProduct, ...] = (
    SubscriptionProduct("Netflix", "ENTERTAINMENT", "STREAMING_VIDEO", 16.99),
    SubscriptionProduct("Spotify", "ENTERTAINMENT", "STREAMING_AUDIO", 10.99),
    SubscriptionProduct("Apple iCloud", "BILLS_AND_UTILITIES", "CLOUD_STORAGE", 9.99),
    SubscriptionProduct("Adobe Creative Cloud", "BILLS_AND_UTILITIES", "SOFTWARE", 54.99),
    SubscriptionProduct("Calm App", "HEALTHCARE", "MENTAL_HEALTH", 14.99),
    SubscriptionProduct("Peloton", "HEALTHCARE", "FITNESS", 44.00),
    SubscriptionProduct("Disney+", "ENTERTAINMENT", "STREAMING_VIDEO", 13.99),
    SubscriptionProduct("Amazon Prime", "SHOPPING", "MEMBERSHIP", 14.99, cadence_days=30),
    SubscriptionProduct("Notion", "BILLS_AND_UTILITIES", "SOFTWARE", 9.99),
)


PERSONA_TEMPLATES: Dict[str, PersonaTemplate] = {
    "Debt Fighter": PersonaTemplate(
        name="Debt Fighter",
        priority=1,
        income_range=(3600, 5200),
        savings_rate=(0.01, 0.05),
        buffer_months=(0.2, 0.8),
        credit_utilization=(0.65, 0.95),
        card_spend_bias=0.75,
        subscription_merchants=(1, 3),
        subscription_share=(0.03, 0.08),
        income_variance=0.08,
        pay_gap_days=(12, 17),
        variable_income=False,
        force_interest=True,
        allow_overdue=True,
    ),
    "Gig Worker": PersonaTemplate(
        name="Gig Worker",
        priority=2,
        income_range=(4200, 6800),
        savings_rate=(0.02, 0.08),
        buffer_months=(0.1, 0.8),
        credit_utilization=(0.25, 0.55),
        card_spend_bias=0.55,
        subscription_merchants=(1, 3),
        subscription_share=(0.04, 0.09),
        income_variance=0.35,
        pay_gap_days=(20, 45),
        variable_income=True,
        allow_overdue=False,
    ),
    "Auto-Payer": PersonaTemplate(
        name="Auto-Payer",
        priority=3,
        income_range=(5500, 9000),
        savings_rate=(0.05, 0.12),
        buffer_months=(0.8, 1.5),
        credit_utilization=(0.25, 0.55),
        card_spend_bias=0.65,
        subscription_merchants=(3, 6),
        subscription_share=(0.12, 0.25),
        income_variance=0.1,
        pay_gap_days=(14, 18),
        variable_income=False,
    ),
    "Wealth Compounder": PersonaTemplate(
        name="Wealth Compounder",
        priority=4,
        income_range=(12000, 20000),
        savings_rate=(0.02, 0.08),
        buffer_months=(4.0, 7.0),
        credit_utilization=(0.05, 0.25),
        card_spend_bias=0.35,
        subscription_merchants=(2, 4),
        subscription_share=(0.05, 0.12),
        income_variance=0.06,
        pay_gap_days=(12, 17),
        variable_income=False,
        ensure_positive_savings=True,
    ),
    "Optimizer": PersonaTemplate(
        name="Optimizer",
        priority=5,
        income_range=(6500, 9500),
        savings_rate=(0.15, 0.30),
        buffer_months=(1.5, 3.0),
        credit_utilization=(0.02, 0.18),
        card_spend_bias=0.25,
        subscription_merchants=(1, 3),
        subscription_share=(0.04, 0.10),
        income_variance=0.08,
        pay_gap_days=(14, 18),
        variable_income=False,
        ensure_positive_savings=True,
    ),
}


def clamp_user_count(value: int) -> int:
    """Clamp the requested user count to the supported min/max bounds."""
    return max(MIN_USERS, min(MAX_USERS, value))


def expand_personas(user_count: int, rng: random.Random) -> List[PersonaTemplate]:
    """Return a persona list sized to the requested user count."""
    weights = [
        ("Debt Fighter", 0.24),
        ("Gig Worker", 0.18),
        ("Auto-Payer", 0.2),
        ("Wealth Compounder", 0.18),
        ("Optimizer", 0.2),
    ]
    assignments: List[PersonaTemplate] = []
    for name, weight in weights:
        target = max(1, int(math.floor(user_count * weight)))
        assignments.extend(PERSONA_TEMPLATES[name] for _ in range(target))

    while len(assignments) < user_count:
        assignments.append(PERSONA_TEMPLATES["Optimizer"])
    rng.shuffle(assignments)
    return assignments[:user_count]


def random_mask(rng: random.Random) -> str:
    return "".join(str(rng.randint(0, 9)) for _ in range(4))


def make_user_record(
    user_idx: int,
    template: PersonaTemplate,
    faker: Faker,
) -> UserRecord:
    user_id = str(uuid.uuid5(USER_NAMESPACE, f"{template.name}-{user_idx}"))
    full_name = faker.name()
    email = f"{full_name.lower().replace(' ', '.')}.{user_idx}@spendsense.test"
    consent_ts = datetime.now(UTC).isoformat(timespec="seconds")
    location = faker.city(), faker.state_abbr()
    return UserRecord(
        user_id=user_id,
        full_name=full_name,
        email=email,
        persona_hint=template.name,
        persona_priority=template.priority,
        consent_granted=True,
        consent_ts=consent_ts,
        city=location[0],
        region=location[1],
    )


def build_accounts(
    user: UserRecord,
    template: PersonaTemplate,
    monthly_income: float,
    savings_rate: float,
    buffer_months: float,
    rng: random.Random,
) -> Dict[str, AccountRecord]:
    monthly_expense = monthly_income * (1 - savings_rate)
    checking_balance = monthly_expense * buffer_months * rng.uniform(0.85, 1.15)
    savings_balance = monthly_income * savings_rate * rng.uniform(2.0, 4.0)
    credit_limit = rng.randint(4000, 12000)
    utilization = rng.uniform(*template.credit_utilization)
    credit_balance = credit_limit * utilization

    accounts = {
        "checking": AccountRecord(
            account_id=str(uuid.uuid5(ACCOUNT_NAMESPACE, f"{user.user_id}-checking")),
            user_id=user.user_id,
            name=f"{user.full_name.split()[0]}'s Checking",
            type="depository",
            subtype="checking",
            mask=random_mask(rng),
            available_balance=round_currency(checking_balance),
            current_balance=round_currency(checking_balance),
            limit=0.0,
            iso_currency_code=USD,
            holder_category="personal",
        ),
        "savings": AccountRecord(
            account_id=str(uuid.uuid5(ACCOUNT_NAMESPACE, f"{user.user_id}-savings")),
            user_id=user.user_id,
            name=f"{user.full_name.split()[0]}'s Savings",
            type="depository",
            subtype="savings",
            mask=random_mask(rng),
            available_balance=round_currency(max(savings_balance, 0.0)),
            current_balance=round_currency(max(savings_balance, 0.0)),
            limit=0.0,
            iso_currency_code=USD,
            holder_category="personal",
        ),
        "credit": AccountRecord(
            account_id=str(uuid.uuid5(ACCOUNT_NAMESPACE, f"{user.user_id}-credit")),
            user_id=user.user_id,
            name=f"{user.full_name.split()[0]}'s Rewards Card",
            type="credit",
            subtype="credit card",
            mask=random_mask(rng),
            available_balance=round_currency(max(credit_limit - credit_balance, 0.0)),
            current_balance=round_currency(credit_balance),
            limit=float(credit_limit),
            iso_currency_code=USD,
            holder_category="personal",
        ),
    }
    return accounts


def round_currency(amount: float) -> float:
    return round(amount, 2)


def daterange(end_days: int) -> Iterable[date]:
    today = date.today()
    for offset in range(end_days):
        yield today - timedelta(days=offset)


def build_pay_dates(
    horizon_days: int,
    template: PersonaTemplate,
    rng: random.Random,
) -> List[date]:
    lower, upper = template.pay_gap_days
    end_date = date.today() - timedelta(days=horizon_days)
    cursor = date.today()
    pay_dates: List[date] = []
    while cursor > end_date:
        gap = rng.randint(lower, upper)
        cursor -= timedelta(days=gap)
        if cursor <= end_date:
            break
        pay_dates.append(cursor)
    if not pay_dates:
        pay_dates.append(date.today() - timedelta(days=horizon_days // 2))
    return sorted(pay_dates)


def generate_income_transactions(
    user: UserRecord,
    checking_account: AccountRecord,
    template: PersonaTemplate,
    monthly_income: float,
    horizon_days: int,
    rng: random.Random,
    faker: Faker,
) -> List[TransactionRecord]:
    pay_dates = build_pay_dates(horizon_days, template, rng)
    target_total = monthly_income * (horizon_days / 30.0)
    base_amount = target_total / len(pay_dates)
    employer = faker.company()
    records: List[TransactionRecord] = []
    for idx, pay_date in enumerate(pay_dates):
        variance_multiplier = 1 + rng.uniform(-template.income_variance, template.income_variance)
        amount = round_currency(base_amount * max(0.35, variance_multiplier))
        txn_id = str(
            uuid.uuid5(TRANSACTION_NAMESPACE, f"{checking_account.account_id}-pay-{pay_date}-{idx}")
        )
        records.append(
            TransactionRecord(
                transaction_id=txn_id,
                user_id=user.user_id,
                account_id=checking_account.account_id,
                date=pay_date,
                amount=amount,
                merchant_name=employer,
                category_primary="INCOME",
                category_detailed="SALARY",
                payment_channel="ach",
                is_subscription=False,
                pending=False,
                currency_code=USD,
                recurring_group_id=f"PAYROLL-{user.user_id}",
            )
        )
    return records


def generate_subscription_transactions(
    user: UserRecord,
    account: AccountRecord,
    template: PersonaTemplate,
    total_target: float,
    horizon_days: int,
    rng: random.Random,
) -> List[TransactionRecord]:
    n_merchants = min(
        len(SUBSCRIPTION_PRODUCTS),
        rng.randint(*template.subscription_merchants),
    )
    products = rng.sample(SUBSCRIPTION_PRODUCTS, n_merchants)
    records: List[TransactionRecord] = []
    total_created = 0.0
    start_date = date.today() - timedelta(days=horizon_days)
    for product in products:
        anchor = date.today() - timedelta(days=rng.randint(0, 29))
        current = anchor
        while current >= start_date:
            amount = round_currency(product.base_amount * rng.uniform(0.9, 1.15))
            txn_id = str(
                uuid.uuid5(
                    TRANSACTION_NAMESPACE,
                    f"{account.account_id}-{product.name}-{current.isoformat()}",
                )
            )
            records.append(
                TransactionRecord(
                    transaction_id=txn_id,
                    user_id=user.user_id,
                    account_id=account.account_id,
                    date=current,
                    amount=-amount,
                    merchant_name=product.name,
                    category_primary=product.primary,
                    category_detailed=product.detailed,
                    payment_channel="card",
                    is_subscription=True,
                    pending=False,
                    currency_code=USD,
                    recurring_group_id=f"SUB-{product.name}",
                )
            )
            total_created += amount
            current -= timedelta(days=product.cadence_days)
    # Ensure subscription share meets minimum target
    if total_created < total_target:
        filler_amount = round_currency(total_target - total_created)
        txn_id = str(
            uuid.uuid5(TRANSACTION_NAMESPACE, f"{account.account_id}-Subscription Bundle")
        )
        records.append(
            TransactionRecord(
                transaction_id=txn_id,
                user_id=user.user_id,
                account_id=account.account_id,
                date=date.today() - timedelta(days=15),
                amount=-filler_amount,
                merchant_name="Bundled Subscriptions",
                category_primary="BILLS_AND_UTILITIES",
                category_detailed="SOFTWARE",
                payment_channel="card",
                is_subscription=True,
                pending=False,
                currency_code=USD,
                recurring_group_id=f"SUB-BUNDLE-{user.user_id}",
            )
        )
    return records


def generate_expense_transactions(
    user: UserRecord,
    accounts: Dict[str, AccountRecord],
    template: PersonaTemplate,
    target_total: float,
    rng: random.Random,
) -> List[TransactionRecord]:
    records: List[TransactionRecord] = []
    remaining = target_total
    serial = 0
    categories = list(EXPENSE_CATEGORIES)
    while remaining > 20 and serial < 60:
        serial += 1
        category = rng.choice(categories)
        merchant = rng.choice(category.merchants)
        amount = min(remaining, rng.uniform(category.min_amount, category.max_amount))
        account_key = (
            "credit"
            if rng.random() < template.card_spend_bias
            else "checking"
        )
        account = accounts[account_key]
        txn_id = str(
            uuid.uuid5(
                TRANSACTION_NAMESPACE,
                f"{account.account_id}-{merchant}-{serial}",
            )
        )
        records.append(
            TransactionRecord(
                transaction_id=txn_id,
                user_id=user.user_id,
                account_id=account.account_id,
                date=date.today() - timedelta(days=rng.randint(1, DEFAULT_HORIZON_DAYS)),
                amount=-round_currency(amount),
                merchant_name=merchant,
                category_primary=category.primary,
                category_detailed=category.detailed,
                payment_channel="card" if account_key == "credit" else "online",
                is_subscription=False,
                pending=False,
                currency_code=USD,
                recurring_group_id=None,
            )
        )
        remaining -= amount
    return records


def generate_interest_transaction(
    user: UserRecord,
    credit_account: AccountRecord,
    rng: random.Random,
) -> TransactionRecord:
    interest_amount = round_currency(credit_account.current_balance * rng.uniform(0.015, 0.025))
    txn_id = str(
        uuid.uuid5(
            TRANSACTION_NAMESPACE,
            f"{credit_account.account_id}-interest-{date.today()}",
        )
    )
    return TransactionRecord(
        transaction_id=txn_id,
        user_id=user.user_id,
        account_id=credit_account.account_id,
        date=date.today() - timedelta(days=25),
        amount=-interest_amount,
        merchant_name="Card Interest Charge",
        category_primary="FINANCE",
        category_detailed="INTEREST",
        payment_channel="card",
        is_subscription=False,
        pending=False,
        currency_code=USD,
        recurring_group_id="INTEREST",
    )


def build_liability_record(
    credit_account: AccountRecord,
    template: PersonaTemplate,
    rng: random.Random,
) -> LiabilityRecord:
    apr = rng.uniform(14.0, 24.0)
    if template.name == "Wealth Compounder":
        apr = rng.uniform(9.0, 15.0)
    elif template.name == "Optimizer":
        apr = rng.uniform(11.0, 17.0)
    min_payment = max(25.0, credit_account.current_balance * 0.02)
    last_payment = min_payment * rng.uniform(0.8, 1.2)
    is_overdue = template.allow_overdue and rng.random() < 0.35
    return LiabilityRecord(
        account_id=credit_account.account_id,
        apr_type="variable",
        apr_percentage=round_currency(apr),
        minimum_payment_amount=round_currency(min_payment),
        last_payment_amount=round_currency(last_payment),
        last_statement_balance=round_currency(credit_account.current_balance),
        is_overdue=is_overdue,
        next_payment_due_date=date.today() + timedelta(days=rng.randint(5, 20)),
    )


def generate_user_bundle(
    user_idx: int,
    template: PersonaTemplate,
    rng: random.Random,
    faker: Faker,
    horizon_days: int,
) -> Tuple[List[UserRecord], List[AccountRecord], List[TransactionRecord], List[LiabilityRecord]]:
    user = make_user_record(user_idx, template, faker)
    monthly_income = rng.uniform(*template.income_range)
    savings_rate = rng.uniform(*template.savings_rate)
    if template.ensure_positive_savings:
        savings_rate = max(savings_rate, 0.12)
    buffer_months = rng.uniform(*template.buffer_months)
    accounts = build_accounts(user, template, monthly_income, savings_rate, buffer_months, rng)

    income_txns = generate_income_transactions(
        user,
        accounts["checking"],
        template,
        monthly_income,
        horizon_days,
        rng,
        faker,
    )
    total_income = sum(tx.amount for tx in income_txns)
    total_expense_target = total_income * (1 - savings_rate)

    subscription_ratio = rng.uniform(*template.subscription_share)
    subscription_target = total_expense_target * subscription_ratio
    subscription_transactions = generate_subscription_transactions(
        user,
        accounts["credit"],
        template,
        subscription_target,
        horizon_days,
        rng,
    )

    discretionary_target = max(0.0, total_expense_target - sum(-tx.amount for tx in subscription_transactions))
    expense_transactions = generate_expense_transactions(
        user,
        accounts,
        template,
        discretionary_target,
        rng,
    )

    transactions = income_txns + subscription_transactions + expense_transactions
    if template.force_interest:
        transactions.append(generate_interest_transaction(user, accounts["credit"], rng))

    liabilities = [build_liability_record(accounts["credit"], template, rng)]
    return [user], list(accounts.values()), transactions, liabilities


def write_csv(path: Path, field_names: Sequence[str], rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(rows)


def generate_dataset(
    user_count: int,
    seed: int,
    output_dir: Path,
    horizon_days: int = DEFAULT_HORIZON_DAYS,
) -> None:
    rng = random.Random(seed)
    faker = Faker()
    faker.seed_instance(seed)

    personas = expand_personas(user_count, rng)

    users: List[UserRecord] = []
    accounts: List[AccountRecord] = []
    transactions: List[TransactionRecord] = []
    liabilities: List[LiabilityRecord] = []

    for idx, template in enumerate(personas):
        bundle = generate_user_bundle(idx, template, rng, faker, horizon_days)
        users.extend(bundle[0])
        accounts.extend(bundle[1])
        transactions.extend(bundle[2])
        liabilities.extend(bundle[3])

    write_csv(
        output_dir / "users.csv",
        list(asdict(users[0]).keys()),
        (asdict(record) for record in users),
    )
    write_csv(
        output_dir / "accounts.csv",
        list(asdict(accounts[0]).keys()),
        (asdict(record) for record in accounts),
    )
    write_csv(
        output_dir / "transactions.csv",
        [
            "transaction_id",
            "user_id",
            "account_id",
            "date",
            "amount",
            "merchant_name",
            "category_primary",
            "category_detailed",
            "payment_channel",
            "is_subscription",
            "pending",
            "currency_code",
            "recurring_group_id",
        ],
        (
            {
                **asdict(record),
                "date": record.date.isoformat(),
            }
            for record in transactions
        ),
    )
    write_csv(
        output_dir / "liabilities.csv",
        list(asdict(liabilities[0]).keys()),
        (
            {
                **asdict(record),
                "next_payment_due_date": record.next_payment_due_date.isoformat(),
            }
            for record in liabilities
        ),
    )

    print(
        f"Generated {len(users)} users, {len(accounts)} accounts, "
        f"{len(transactions)} transactions, and {len(liabilities)} liabilities "
        f"into {output_dir}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic Plaid-style data for SpendSense.")
    parser.add_argument(
        "--users",
        type=int,
        default=DEFAULT_USER_COUNT,
        help=f"Number of synthetic users ({MIN_USERS}-{MAX_USERS}).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed for deterministic outputs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory for generated CSV files.",
    )
    parser.add_argument(
        "--horizon-days",
        type=int,
        default=DEFAULT_HORIZON_DAYS,
        help="Length of transaction history window to generate.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    user_count = clamp_user_count(args.users)
    if user_count != args.users:
        print(f"Requested {args.users} users; clamped to {user_count}.")
    generate_dataset(
        user_count=user_count,
        seed=args.seed,
        output_dir=args.output_dir,
        horizon_days=args.horizon_days,
    )


if __name__ == "__main__":
    main()
