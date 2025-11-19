"""Synthetic data generator for SpendSense.

Creates Plaid-style synthetic data with persona-specific signals so downstream
pipelines can deterministically classify users and create explanations.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from faker import Faker


@dataclass
class GenerationConfig:
    """Runtime configuration for the generator."""

    num_users: int = 75
    seed: int = 42
    output_dir: Path = Path("data/generated")

    def __post_init__(self) -> None:
        if not 50 <= self.num_users <= 100:
            raise ValueError("num_users must be between 50 and 100")
        self.output_dir = Path(self.output_dir)


@dataclass
class PersonaDefinition:
    code: str
    title: str
    weight: int
    income_range: Sequence[int]
    net_savings_rate: Sequence[float]
    subscriptions_range: Sequence[int]
    credit_utilization: Sequence[float]
    interest_paid: Sequence[int]
    volatility: Sequence[float]
    buffer_months: Sequence[float]


PERSONAS: List[PersonaDefinition] = [
    PersonaDefinition(
        code="debt_fighter",
        title="Debt Fighter",
        weight=3,
        income_range=(45000, 90000),
        net_savings_rate=(-0.20, 0.05),
        subscriptions_range=(1, 3),
        credit_utilization=(0.55, 0.95),
        interest_paid=(150, 600),
        volatility=(0.05, 0.15),
        buffer_months=(0.2, 1.0),
    ),
    PersonaDefinition(
        code="gig_worker",
        title="Gig Worker",
        weight=2,
        income_range=(30000, 80000),
        net_savings_rate=(-0.10, 0.10),
        subscriptions_range=(1, 4),
        credit_utilization=(0.25, 0.55),
        interest_paid=(0, 50),
        volatility=(0.25, 0.65),
        buffer_months=(0.5, 1.5),
    ),
    PersonaDefinition(
        code="auto_payer",
        title="Auto-Payer",
        weight=2,
        income_range=(60000, 110000),
        net_savings_rate=(0.00, 0.15),
        subscriptions_range=(5, 12),
        credit_utilization=(0.20, 0.45),
        interest_paid=(0, 20),
        volatility=(0.05, 0.10),
        buffer_months=(1.0, 2.0),
    ),
    PersonaDefinition(
        code="wealth_compounder",
        title="Wealth Compounder",
        weight=2,
        income_range=(120000, 250000),
        net_savings_rate=(0.05, 0.20),
        subscriptions_range=(2, 6),
        credit_utilization=(0.05, 0.25),
        interest_paid=(0, 10),
        volatility=(0.05, 0.15),
        buffer_months=(4.0, 12.0),
    ),
    PersonaDefinition(
        code="optimizer",
        title="Optimizer",
        weight=1,
        income_range=(65000, 120000),
        net_savings_rate=(0.10, 0.25),
        subscriptions_range=(1, 4),
        credit_utilization=(0.05, 0.35),
        interest_paid=(0, 5),
        volatility=(0.05, 0.10),
        buffer_months=(2.0, 6.0),
    ),
]


class SyntheticDataGenerator:
    def __init__(self, config: GenerationConfig) -> None:
        self.config = config
        self.fake = Faker()
        self.random = random.Random(config.seed)
        self.fake.seed_instance(config.seed)

    def run(self) -> None:
        users: List[Dict] = []
        accounts: List[Dict] = []
        transactions: List[Dict] = []

        persona_queue = self._build_persona_queue()

        for user_index in range(self.config.num_users):
            persona = persona_queue[user_index]
            user, acct, txns = self._generate_user_bundle(user_index, persona)
            users.append(user)
            accounts.extend(acct)
            transactions.extend(txns)

        self._write_output(users, accounts, transactions)

    # ------------------------------------------------------------------
    def _build_persona_queue(self) -> List[PersonaDefinition]:
        """Guarantee coverage of all personas and fill remaining via weights."""

        seed_personas = PERSONAS.copy()
        remaining_slots = self.config.num_users - len(seed_personas)
        weights = [p.weight for p in PERSONAS]

        for _ in range(max(0, remaining_slots)):
            choice = self.random.choices(PERSONAS, weights=weights, k=1)[0]
            seed_personas.append(choice)

        self.random.shuffle(seed_personas)
        return seed_personas[: self.config.num_users]

    # ------------------------------------------------------------------
    def _generate_user_bundle(
        self, user_index: int, persona: PersonaDefinition
    ) -> Tuple[Dict, List[Dict], List[Dict]]:
        user_id = f"user_{user_index:03d}"
        base_income = self.random.randint(*persona.income_range)
        savings_rate = self.random.uniform(*persona.net_savings_rate)
        monthly_expenses = base_income * (1 - savings_rate)
        credit_limit = self.random.randint(4000, 25000)
        credit_util = self.random.uniform(*persona.credit_utilization)
        credit_balance = round(credit_limit * credit_util, 2)
        interest_paid = round(self.random.uniform(*persona.interest_paid), 2)
        volatility = round(self.random.uniform(*persona.volatility), 2)
        subscriptions = self.random.randint(*persona.subscriptions_range)
        buffer_months = round(self.random.uniform(*persona.buffer_months), 2)

        user_record = {
            "user_id": user_id,
            "full_name": self.fake.name(),
            "email": self.fake.email(domain="spendsense.ai"),
            "persona_hint": persona.code,
            "annual_income": base_income,
            "monthly_expenses": round(monthly_expenses / 12, 2),
            "net_savings_rate": round(savings_rate, 3),
            "subscriptions": subscriptions,
            "credit_limit": credit_limit,
            "credit_balance": credit_balance,
            "interest_paid": interest_paid,
            "income_volatility": volatility,
            "cash_buffer_months": buffer_months,
        }

        account_records = self._generate_accounts(
            user_id, credit_balance, credit_limit, persona
        )
        transaction_records = self._generate_transactions(
            user_id,
            account_records,
            monthly_expenses,
            subscriptions,
            persona,
        )

        return user_record, account_records, transaction_records

    # ------------------------------------------------------------------
    def _generate_accounts(
        self,
        user_id: str,
        credit_balance: float,
        credit_limit: int,
        persona: PersonaDefinition,
    ) -> List[Dict]:
        accounts = [
            {
                "account_id": f"{user_id}_chk",
                "user_id": user_id,
                "type": "checking",
                "institution": "SpendSense Bank",
                "balance": round(self.random.uniform(1500, 8000), 2),
                "credit_limit": 0,
            },
            {
                "account_id": f"{user_id}_sav",
                "user_id": user_id,
                "type": "savings",
                "institution": "SpendSense Bank",
                "balance": round(self.random.uniform(2000, 30000), 2),
                "credit_limit": 0,
            },
            {
                "account_id": f"{user_id}_cc",
                "user_id": user_id,
                "type": "credit",
                "institution": "SpendSense Rewards",
                "balance": round(-credit_balance, 2),
                "credit_limit": credit_limit,
            },
        ]

        # Wealth compounders often have brokerage accounts
        if persona.code == "wealth_compounder" and self.random.random() > 0.4:
            accounts.append(
                {
                    "account_id": f"{user_id}_bro",
                    "user_id": user_id,
                    "type": "brokerage",
                    "institution": "SpendSense Invest",
                    "balance": round(self.random.uniform(15000, 120000), 2),
                    "credit_limit": 0,
                }
            )

        return accounts

    # ------------------------------------------------------------------
    def _generate_transactions(
        self,
        user_id: str,
        accounts: List[Dict],
        monthly_expenses: float,
        subscriptions: int,
        persona: PersonaDefinition,
    ) -> List[Dict]:
        """Create ~120 days of transactions with persona-specific flair."""

        categories = [
            "groceries",
            "rent",
            "utilities",
            "entertainment",
            "travel",
            "subscriptions",
            "income",
            "dining",
            "transport",
        ]
        subscription_merchants = [
            "Netflix",
            "Spotify",
            "Adobe",
            "GymCo",
            "CloudStorage.io",
            "News+",
            "MealKit",
            "PrimeBox",
        ]

        horizon = 120
        today = datetime.now(UTC).date()
        txns: List[Dict] = []
        user_accounts = {acct["type"]: acct for acct in accounts}

        for days_back in range(horizon):
            tx_date = today - timedelta(days=days_back)

            # Income roughly bi-weekly.
            if days_back % 14 == 0:
                income_amount = self._sample_income_amount(persona)
                txns.append(
                    self._transaction(
                        user_id,
                        user_accounts["checking"],
                        tx_date,
                        amount=income_amount,
                        category="income",
                        merchant=self.fake.company(),
                        is_subscription=False,
                    )
                )

            # Recurring subscriptions
            if subscriptions and days_back % 30 == 0:
                for merchant in self.random.sample(
                    subscription_merchants, k=min(subscriptions, len(subscription_merchants))
                ):
                    amount = round(self.random.uniform(8, 45), 2)
                    txns.append(
                        self._transaction(
                            user_id,
                            user_accounts["credit"],
                            tx_date,
                            amount=-amount,
                            category="subscriptions",
                            merchant=merchant,
                            is_subscription=True,
                        )
                    )

            # Daily spend variance
            spend = self.random.gauss(mu=monthly_expenses / 30, sigma=monthly_expenses / 90)
            spend = max(5, min(spend, monthly_expenses / 4))
            txns.append(
                self._transaction(
                    user_id,
                    user_accounts["credit"],
                    tx_date,
                    amount=-round(spend, 2),
                    category=self.random.choice(categories[:-2]),
                    merchant=self.fake.company(),
                    is_subscription=False,
                )
            )

        # Interest payments for debt fighters
        if persona.code == "debt_fighter":
            for month in range(4):
                tx_date = today - timedelta(days=30 * month + 5)
                txns.append(
                    self._transaction(
                        user_id,
                        user_accounts["credit"],
                        tx_date,
                        amount=-round(self.random.uniform(40, 120), 2),
                        category="interest",
                        merchant="SpendSense Rewards",
                        is_subscription=False,
                    )
                )

        return txns

    # ------------------------------------------------------------------
    def _transaction(
        self,
        user_id: str,
        account: Dict,
        date: datetime.date,
        amount: float,
        category: str,
        merchant: str,
        is_subscription: bool,
    ) -> Dict:
        return {
            "transaction_id": f"{user_id}_{abs(hash((user_id, merchant, date, amount))):x}",
            "user_id": user_id,
            "account_id": account["account_id"],
            "date": date.isoformat(),
            "amount": round(amount, 2),
            "category": category,
            "merchant": merchant,
            "is_subscription": is_subscription,
        }

    def _sample_income_amount(self, persona: PersonaDefinition) -> float:
        base = self.random.randint(*persona.income_range) / 24  # bi-weekly
        volatility = self.random.uniform(*persona.volatility)
        noise = self.random.gauss(mu=0, sigma=base * volatility)
        return round(base + noise, 2)

    # ------------------------------------------------------------------
    def _write_output(self, users: List[Dict], accounts: List[Dict], transactions: List[Dict]) -> None:
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        bundle = {
            "generated_at": datetime.now(UTC).isoformat(),
            "num_users": len(users),
            "users": users,
            "accounts": accounts,
            "transactions": transactions,
        }

        self._write_csv(self.config.output_dir / "users.csv", users)
        self._write_csv(self.config.output_dir / "accounts.csv", accounts)
        self._write_csv(self.config.output_dir / "transactions.csv", transactions)

        with open(self.config.output_dir / "bundle.json", "w", encoding="utf-8") as fp:
            json.dump(bundle, fp, indent=2)

    def _write_csv(self, path: Path, rows: Iterable[Dict]) -> None:
        rows = list(rows)
        if not rows:
            return
        with open(path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)


# ---------------------------------------------------------------------------

def parse_args() -> GenerationConfig:
    parser = argparse.ArgumentParser(description="Generate synthetic SpendSense data")
    parser.add_argument("--users", type=int, default=75, help="Number of users to generate (50-100)")
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/generated"),
        help="Directory to store generated CSV/JSON files",
    )
    args = parser.parse_args()
    return GenerationConfig(num_users=args.users, seed=args.seed, output_dir=args.output_dir)


def main() -> None:
    config = parse_args()
    generator = SyntheticDataGenerator(config)
    generator.run()
    print(f"Generated dataset for {config.num_users} users in {config.output_dir}")


if __name__ == "__main__":
    main()
