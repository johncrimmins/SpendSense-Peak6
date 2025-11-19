# SpendSense

SpendSense is a local-first financial intelligence engine that ingests synthetic Plaid-style transaction data, assigns deterministic personas, and delivers explainable recommendations through a FastAPI + Jinja2 + htmx experience. A Streamlit operator console provides auditable oversight.

## Getting Started

1. **Create a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Project Layout**
   ```
   ingest/        # data generation & loading
   engine/        # features, personas, recommendations
   web/           # FastAPI app + templates
   guardrails/    # compliance utilities
   operator_app/  # Streamlit oversight app (renamed to avoid stdlib conflict)
   docs/          # ADRs, architecture, PRD
   ```
4. **Next Steps**
   - Implement the synthetic data generator in `ingest/generator.py`.
   - Build the loader to populate `spendsense.db`.
   - Continue following Taskmaster tasks in `.taskmaster/tasks/tasks.json`.

## Tooling
- **FastAPI** for serving the main app.
- **TailwindCSS + htmx** for “Stunning” UI interactions.
- **SQLite** as the local persistence layer.
- **Taskmaster** for project planning (see `.taskmaster/`).

