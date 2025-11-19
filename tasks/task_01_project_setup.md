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
        "description": "Build ingest/generator.py to produce deterministic synthetic Plaid-style data spanning all personas.",
        "details": "- Use Faker with a fixed seed to create 50-100 users, accounts, and transactions.\n- Encode persona blueprints so downstream metrics (utilization, subscriptions, gig work volatility) are testable.\n- Export CSVs for users, accounts, and transactions under data/synthetic/.\n- Provide a CLI entry point so the generator can be rerun with different volumes.",
        "testStrategy": "Run `python3 ingest/generator.py --num-users 60` and spot-check the generated CSVs for persona coverage and row counts.",
        "status": "done",
        "dependencies": [1],
        "priority": "high",
        "subtasks": []
      },
      {
        "id": 3,
        "title": "Implement Data Loader",
        "description": "Normalize the generated CSVs into SQLite tables so subsequent phases can query a single spendsense.db file.",
        "details": "- Create ingest/loader.py with CLI flags for CSV directory, DB path, and --reset.\n- Define schema for users/accounts/transactions including indexes and foreign keys.\n- Bulk insert data idempotently using INSERT OR REPLACE and optional reset logic.\n- Enable downstream verification via sqlite3 queries.",
        "testStrategy": "Run `python3 ingest/loader.py --csv-dir data/synthetic --db spendsense.db --reset` then query counts with sqlite3.",
        "status": "done",
        "dependencies": [1, 2],
        "priority": "high",
        "subtasks": []
      }
    ],
    "metadata": {
      "created": "2025-11-19T15:50:37.855Z",
      "description": "Default tasks context",
      "updated": "2025-11-19T17:40:00.000Z"
    }
  }
}
