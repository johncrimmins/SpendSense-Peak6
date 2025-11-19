# Project Brief: SpendSense

## Overview
SpendSense is a financial intelligence engine designed to bridge the gap between raw transaction data (Plaid-style) and personalized, actionable financial advice. It detects behavioral patterns in transaction history, assigns users to specific financial personas, and delivers explainable recommendations with a "Stunning," modern fintech UI.

## Core Goals
1.  **Data Ingestion**: Generate and process synthetic transaction data for 50-100 users.
2.  **Behavioral Signal Detection**: Identify patterns like "High Utilization," "Subscription Heavy," or "Wealth Compounder."
3.  **Persona Assignment**: Deterministically assign users to one of 5 priority personas.
4.  **Explainable Recommendations**: Provide specific, math-backed rationales for every suggestion (e.g., "You could save $87/month...").
5.  **Stunning UI**: Build a mobile-first, high-polish web interface (FastAPI + Jinja2 + Tailwind + htmx).
6.  **Operator Oversight**: Provide a Streamlit-based admin view for auditing and overriding decisions.

## Key Constraints
*   **No "Black Box"**: All logic must be explainable.
*   **Privacy**: Use 100% synthetic data.
*   **Local Execution**: System must run locally without external dependencies.
*   **Tone**: Educational, empowering, non-judgmental.

