{
  "master": {
    "tasks": [
      {
        "id": 1,
        "title": "Project Setup",
        "description": "Set up the Python environment, requirements.txt, and project directory structure as defined in systemPatterns.md. Initialize git if not already done.",
        "details": "- Create requirements.txt with: fastapi, uvicorn, pandas, sqlalchemy, jinja2, faker, aiosqlite, pytest, httpx.\n- Create directory structure: ingest/, engine/, web/, guardrails/, operator/, docs/.\n- Create .gitignore.",
        "testStrategy": "Verify environment activation and package installation.",
        "status": "pending",
        "dependencies": [],
        "priority": "high",
        "subtasks": []
      }
    ],
    "metadata": {
      "created": "2025-11-19T15:50:37.855Z",
      "description": "Default tasks context",
      "updated": "2025-11-19T15:50:37.855Z"
    }
  }
}