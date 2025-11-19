# Product Context

## Problem Statement
Banks have access to massive amounts of transaction data but often fail to turn it into useful advice for customers. Generic PFM tools show charts but don't answer "What should I do next?" SpendSense solves this by analyzing behavior and offering concrete next steps.

## The "North Star"
**"Every recommendation must answer 'Why?' with user-specific math."**

## User Personas (The "Brain")
The system assigns users to one primary persona based on a strict priority hierarchy:

1.  **The Debt Fighter (High Utilization)**
    *   **Trigger:** Utilization ≥ 50% OR Interest > $0 OR Past Due.
    *   **Focus:** Triage, "Snowball Method," reducing interest.
2.  **The Gig Worker (Variable Income)**
    *   **Trigger:** High income volatility OR large pay gaps.
    *   **Focus:** Cash flow smoothing, "Safe to Spend" metric.
3.  **The Auto-Payer (Subscription Heavy)**
    *   **Trigger:** ≥ 3 recurring merchants AND ≥ 10% of outflow.
    *   **Focus:** Audit leakage, annual savings visualization.
4.  **The Wealth Compounder (High Value / HENRY)**
    *   **Trigger:** Top 20% Income AND High Cash Buffer AND Low Savings Rate.
    *   **Focus:** APY optimization, tax-advantaged accounts. **Highest LTV.**
5.  **The Optimizer (Savings Builder)**
    *   **Trigger:** Low utilization AND positive net savings.
    *   **Focus:** Gamification, goal setting.

## User Experience (The "Stunning UI")
*   **Visual Style:** Series-B Fintech (e.g., Copilot, Monarch). Dark mode default, glassmorphism, vibrant gradients.
*   **Key Views:**
    *   **The Pulse:** Single "Free to Spend" or "Net Worth" number.
    *   **Insight Feed:** TikTok-style scrollable feed of recommendations.
*   **Interaction:** Immediate feedback, smooth transitions (powered by htmx).

## Operator Experience
*   **Goal:** Allow a "Bank Analyst" to audit decisions in < 5 seconds.
*   **Tool:** Streamlit dashboard.
*   **Capabilities:** View decision traces, override personas, check "tone police" logs.

