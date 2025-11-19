# System Patterns

## Architecture Overview
SpendSense follows a modular "Lightweight Backend, Heavy Visuals" architecture, prioritizing local execution and code clarity.

### Core Modules
1.  **`ingest/` (Data Foundation)**
    *   **Generator:** Uses `Faker` to create deterministic synthetic data (50-100 users).
    *   **Loader:** Normalizes data into SQLite (`Users`, `Accounts`, `Transactions`).
2.  **`engine/` (The Brain)**
    *   **Features:** Vectorized Pandas/SQL operations to calculate metrics (Burn Rate, Runway, etc.).
    *   **Classifier:** Deterministic decision tree for Persona assignment.
    *   **Recommendations:** Rule-based engine generating explainable "Because" strings.
3.  **`web/` (The Stunning UI)**
    *   **Framework:** FastAPI serving Jinja2 templates.
    *   **Styling:** TailwindCSS (via CDN or CLI) for glassmorphism and gradients.
    *   **Interactivity:** **htmx** for dynamic content loading (Insight Feed, Pulse updates) without full page reloads.
    *   **Visualization:** Chart.js for embedded graphs.
4.  **`guardrails/` (Compliance)**
    *   **Tone Police:** Dictionary-based filter for banned words/phrases.
    *   **Consent:** Explicit opt-in tracking.
5.  **`operator/` (Oversight)**
    *   **Framework:** Streamlit connected directly to `spendsense.db`.

## Data Flow
1.  **Ingest:** CSV/JSON -> SQLite.
2.  **Process:** `engine` queries SQLite -> Calculates Features -> Assigns Persona -> Generates Recommendations.
3.  **Serve:** FastAPI reads processed data -> Renders HTML via Jinja2/htmx.

## Key Technical Decisions
*   **FastAPI + Async:** Modern, high-performance Python web server.
*   **SQLite:** Simple, file-based relational database. Zero latency.
*   **htmx:** Adds "app-like" feel (AJAX) to server-rendered HTML, avoiding complex JS build steps.
*   **Streamlit:** Rapid development for the internal admin tool.

