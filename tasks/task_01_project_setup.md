{
  "master": {
    "tasks": [
      {
        "id": 1,
        "title": "Project Setup",
        "description": "Set up the Python environment, requirements.txt, and project directory structure as defined in systemPatterns.md. Initialize git if not already done.",
        "details": "- Create requirements.txt with: fastapi, uvicorn, pandas, sqlalchemy, jinja2, faker, aiosqlite, pytest, httpx.\n- Create directory structure: ingest/, engine/, web/, guardrails/, operator/, docs/.\n- Create .gitignore.",
        "testStrategy": "Verify environment activation and package installation.",
        "status": "done",
        "dependencies": [],
        "priority": "high",
        "subtasks": []
      },
      {
        "id": 2,
        "title": "Implement Data Generator",
        "description": "Author ingest/generator.py that deterministically produces persona-aware synthetic Plaid-style data (users, accounts, transactions) for 50-100 users.",
        "details": "- Encode persona templates for Debt Fighter, Gig Worker, Auto-Payer, Wealth Compounder, Optimizer.\n- Generate CSV outputs (users, accounts, transactions) plus manifest JSON in data/raw/.\n- Provide CLI flags for user count, output dir, seed; default to 75 users and enforce 50-100 constraint.\n- Include recurring subscription logic, gig-income volatility, and credit utilization/interest modeling.\n- Document usage via module docstring.",
        "testStrategy": "Run `python3 -m ingest.generator --users 75 --output data/raw` and inspect generated CSV row counts plus manifest contents.",
        "status": "done",
        "dependencies": [
          1
        ],
        "priority": "high",
        "subtasks": []
      }
    ],
    "metadata": {
      "created": "2025-11-19T15:50:37.855Z",
      "description": "Default tasks context",
      "updated": "2025-11-19T17:05:00.000Z"
    }
  }
}