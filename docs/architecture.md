## 3\. Functional Requirements

### 3.1 Data Ingestion (The Input)

  * **Synthetic Generator:** Must create deterministic Plaid-formatted JSON/CSV.
  * **Fields:** `account_id`, `current_balance`, `iso_currency_code`, `merchant_name`, `amount`, `date`, `category` (taxonomy v2).
  * **Volume:** 50-100 Users to prove statistical significance.

### 3.2 Signal Detection (The Math)

The system must calculate these exact metrics for every user:

1.  **Burn Rate:** 6-month rolling average of all outflows (excluding internal transfers).
2.  **Liquid Runway:** `(Checking + Savings Balance) / Burn Rate`.
3.  **Inefficiency Score:** `(Idle Cash - 3x Burn Rate)`. Positive numbers indicate "Lazy Money."

### 3.3 Recommendation Engine (The Output)

  * **Constraint:** Zero "Black Box" advice.
  * **Structure:**
      * **Headline:** "Stop losing $140/month."
      * **The 'Because':** "You have $45,000 in checking. Keeping only $15,000 (3 months expenses) and moving the rest to a 4.5% HYSA generates passive income."
      * **Action:** "View High-Yield Offers."

### 3.4 Stunning User Interface (The Experience)

  * **Requirement:** The UI must look like a Series-B Fintech Product (e.g., Copilot, Monarch, Robinhood), not a data science dashboard.
  * **Visual Language:**
      * **Dark Mode Default:** Deep slates/blacks with vibrant gradients for data.
      * **Glassmorphism:** Semi-transparent cards for account details.
      * **Motion:** Numbers should "count up" when loading. Charts should animate on entry.
  * **Key Views:**
      * **The Pulse:** A single number showing "Free to Spend" or "Net Worth."
      * **The Insight Feed:** A scrollable TikTok-style feed of the generated recommendations.

### 3.5 Operator Guardrails (The Safety)

  * **Admin Dashboard:** A separate view for the "Bank Analyst."
  * **Capabilities:**
      * View "Decision Trace" (e.g., User A mapped to Persona B because Metric X \> Threshold Y).
      * Override Persona manually.
      * Audit "Tone Check" pass/fail logs.

-----

# PART 2: Technical Architecture Document (TAD)

**Stack Strategy:** "Lightweight Backend, Heavy Visuals."
**Philosophy:** Use Python for logic (strength) and modern CSS for visuals (beauty), avoiding complex JS build chains.

## 1\. Technology Stack

| Component | Selection | Justification |
| :--- | :--- | :--- |
| **Core Language** | **Python 3.11+** | Best-in-class for financial math and data manipulation. |
| **Backend API** | **FastAPI** | Async, high-performance, auto-documents via OpenAPI. |
| **Database** | **SQLite** | Zero-latency, local file storage, relational integrity. |
| **ORM** | **SQLAlchemy (Async)** | Modern database interaction. |
| **Frontend (User)** | **Jinja2 + TailwindCSS** | Server-side rendering allows for "Stunning" UI without a React/Node complex build. |
| **Frontend (Admin)**| **Streamlit** | Rapid development for the internal operator view. |
| **Visualization** | **Chart.js** | Lightweight JS library for the "Stunning" charts (embedded in Jinja). |

-----

## 2\. System Modules

### 2.1 `ingest/` (Data Foundation)

  * **`generator.py`:** Uses `Faker` to seed the 5 personas. **Critical:** Must force the "Wealth Compounder" pattern (High Income + Low Savings Rate) to test the high-value logic.
  * **`loader.py`:** Normalizes CSVs into 3 SQLite tables: `Users`, `Accounts`, `Transactions`.

### 2.2 `engine/` ( The Brain)

  * **`features.py`:** Vectorized Pandas operations.
      * *Optimization:* Calculate metrics on the database layer using SQL aggregations where possible for speed, fallback to Pandas for complex sliding windows.
  * **`classifier.py`:** The Decision Tree.
    ```python
    def classify(user):
        if user.utilization > 0.5: return "Debt Fighter"
        if user.runway > 3.0 and user.income_percentile > 0.8: return "Wealth Compounder"
        # ... hierarchy continues
    ```

### 2.3 `web/` (The Stunning UI)

This is the differentiator. Instead of a basic dashboard, we implement a **Mobile-First Web App**.

  * **Templating:** Use Jinja2 inheritance (`base.html`) for layout.
  * **Styling:** Import TailwindCSS via CDN (for dev speed) or minified local file.
  * **Visual Requirements:**
      * **Gradients:** Use CSS gradients `bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500` for the "High Value" cards.
      * **Cards:** `backdrop-blur-md bg-white/10` for the glassmorphism effect.
      * **Typography:** Inter or SF Pro Display font stack.

### 2.4 `guardrails/` (Compliance)

  * **`tone_police.py`:** A dictionary-based filter checking recommendations against a "Banned Words List" (e.g., "stupid," "poor," "waste").

-----

## 3\. Data Model (Schema)

```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    persona TEXT, -- The computed label
    last_updated DATETIME
);

CREATE TABLE financial_snapshot (
    user_id TEXT,
    calc_date DATE,
    net_worth REAL,
    burn_rate REAL,
    runway_months REAL, -- The "Wealth Compounder" signal
    credit_utilization REAL,
    subscription_count INT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE recommendations (
    rec_id TEXT PRIMARY KEY,
    user_id TEXT,
    title TEXT,
    rationale TEXT, -- The "Because" string
    action_link TEXT,
    tone_check_passed BOOLEAN
);
```

-----

## 4\. Implementation Guidance & Roadmap

This guide is designed for a software engineer to pick up and execute immediately.

### Phase 1: Data & Logic (Days 1-3)

1.  **Setup:** `pip install fastapi uvicorn pandas sqlalchemy jinja2 faker`.
2.  **Generate:** Run the `generate_data.py` script (from previous turn) to create `spendsense.db`.
3.  **Analyze:** Build the `FeatureEngine`. **Verification Step:** Ensure "Wealth Compounder" users show `runway_months > 3.0`.
4.  **Classify:** Implement the Persona Priority Queue.

### Phase 2: The API (Day 4)

1.  **Endpoint:** `GET /api/user/{id}/dashboard`. Returns the JSON payload containing the Persona, calculated metrics, and the specific "Because" rationale.
2.  **Endpoint:** `POST /api/refresh`. Triggers a re-calculation of the engine.

### Phase 3: The "Stunning" UI (Days 5-7)

  * **Layout:** Create `templates/dashboard.html`.
  * **Hero Section:** Display "Net Worth" and "Monthly Burn" using large, thin typography on a dark background.
  * **The Feed:** Render the Recommendations as "Cards."
      * *Debt Fighter Card:* Red gradient border. Alert icon.
      * *Wealth Compounder Card:* Gold/Purple gradient. Graph icon showing compound growth.
  * **Charts:** Integrate `Chart.js`. Create a line chart showing "Projected Net Worth" if they follow the recommendation.

### Phase 4: The Operator View (Day 8)

  * Use **Streamlit**.
  * Connect directly to `spendsense.db`.
  * Table view of all users with a dropdown to filter by "Assigned Persona."
  * **Success Metric:** Analyst can find a "Wealth Compounder" and validate *why* they were chosen in \<5 seconds.

-----

## 5\. Alignment Checklist

| Requirement | PRD Reference | Architecture Solution |
| :--- | :--- | :--- |
| **High Value Persona** | Section 2 (Priority 4) | `engine/features.py` calculates `runway_months`; UI renders Gold Gradient card. |
| **Explainability** | Section 3.3 ("The Because") | `recommendations` table stores the generated rationale string; API serves it. |
| **Stunning UI** | Section 3.4 | **Jinja2 + TailwindCSS + Glassmorphism** architecture (replacing basic dashboard). |
| **Latency** | "Fast generation" | Pre-calculation of `financial_snapshot` table means API reads are O(1). |
| **Privacy** | "Synthetic Data" | `ingest/generator.py` creates 100% fake identities locally. |