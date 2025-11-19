# Active Context

## Current Focus
Implementation of Phase 1: Data & Logic.

## Recent History
*   Review of `project-brief.md`, `PRD.md`, and `architecture.md`.
*   Decision to include **htmx** in the tech stack for better UX.
*   Creation of Memory Bank (`memory-bank/`).
*   Initialization of Task Master project (though facing persistence issues, fallback to internal TODOs).
*   Defined granular tasks for Phase 1.
*   Completed base project setup (directory skeleton, `requirements.txt`, `.gitignore`).
*   Built deterministic synthetic data generator (`ingest/generator.py`) plus initial CSV outputs in `data/raw/`.

## Immediate Next Steps
1.  Execute **Task 3: Implement Data Loader**.
    *   Normalize generated CSVs into SQLite tables (`Users`, `Accounts`, `Transactions`).
    *   Provide CLI/utility entrypoint that re-creates `spendsense.db`.
    *   Ensure idempotent runs (truncate/replace existing tables).

## Active Decisions
*   **htmx Adoption:** Chosen to provide a responsive UI without the overhead of a full SPA framework (React/Vue) for the user-facing app.
*   **Persona "Optimizer":** Confirmed as the 5th persona.
*   **Task Management:** Using internal Todo list due to tool issues with Task Master persistence.
