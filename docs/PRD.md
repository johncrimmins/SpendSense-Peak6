Here is the fully aligned, comprehensive **SpendSense Product Requirements Document (PRD)** and **Technical Architecture Document (TAD)**.

These documents have been harmonized to ensure that every functional requirement in the PRD has a direct technical solution in the Architecture, particularly regarding the **High-Value Persona** and the **Stunning UI** requirement.

-----

# PART 1: Product Requirements Document (PRD)

**Project:** SpendSense | **Version:** 2.0 (Final) | **Status:** Ready for Dev
**Core Value:** Transform raw transaction data into explainable, high-fidelity financial guidance.

## 1\. Executive Summary

SpendSense is a financial intelligence engine that bridges the gap between data aggregation (Plaid) and personalized advice. Unlike generic PFM (Personal Financial Management) tools that simply show charts, SpendSense detects specific behavioral patterns—such as "High-Income Inefficiency" (The Wealth Compounder)—and offers concrete, explainable next steps.

**The North Star:** "Every recommendation must answer 'Why?' with user-specific math."

-----

## 2\. User Personas (The "Brain")

The system must deterministically assign users to **one** primary persona per timeframe based on the hierarchy below.

### Priority 1: The Debt Fighter (High Utilization)

  * **Trigger:** Credit Utilization $\ge 50\%$ OR Interest Charges $> \$0$ OR Past Due status.
  * **User Psychology:** Stressed, avoidant. Needs immediate triage.
  * **Experience:** Red/Orange urgency signals. Focus on "Snowball Method" visualization.

### Priority 2: The Gig Worker (Variable Income)

  * **Trigger:** Income Standard Deviation $> 30\%$ of Mean OR Pay Gap $> 20$ days.
  * **User Psychology:** Anxious about cash flow. Needs smoothing.
  * **Experience:** "Safe to Spend" calculator instead of standard monthly budgets.

### Priority 3: The Auto-Payer (Subscription Heavy)

  * **Trigger:** $\ge 3$ Recurring Merchants AND Subscription % of Outflow $\ge 10\%$.
  * **User Psychology:** Unaware of "leakage." Needs an audit.
  * **Experience:** A "Cancel Flow" interface showing total annual savings.

### Priority 4: The Wealth Compounder (High Value / HENRY)

  * **Trigger:** Top 20% Income AND Cash Buffer $> 3$ Months Expenses AND Savings Rate $< 10\%$.
  * **User Psychology:** Efficient earner, inefficient allocator. Losing money to inflation.
  * **Experience:** Gold/Premium aesthetic. Focus on APY, compounding visualizations, and tax-advantaged buckets.
  * **Why this matters:** This is the highest LTV (Lifetime Value) user for a bank.

### Priority 5: The Optimizer (Savings Builder)

  * **Trigger:** Utilization $< 10\%$ AND Net Savings Positive.
  * **User Psychology:** Stable. Gamify their progress.
  * **Experience:** Progress bars, goal confetti.

