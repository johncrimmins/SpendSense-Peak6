# Active Context

## Current Focus
Phase 1: finish the ingestion stack (loader + feature prep).

## Recent History
*   Reviewed `project-brief.md`, `PRD.md`, and `architecture.md`.
*   Task Master initialized; using Taskmaster tasks directly now that persistence works locally.
*   Repo scaffolded (directories, requirements, .gitignore, README).
*   Implemented the synthetic data generator (`ingest/generator.py`) that emits persona-aware CSV + JSON bundles (tested via CLI).

## Immediate Next Steps
1.  Execute **Task 3: Data Loader** (`ingest/loader.py`) to push generated files into SQLite / SQLAlchemy models.
2.  Start **Task 4: Feature Engine** once the loader stabilizes.
3.  Document dataset schema and assumptions alongside loader work.

## Active Decisions
*   **htmx Adoption:** Still via CDN/templating; no pip package required (removed from requirements).
*   **Persona "Optimizer":** Confirmed as the 5th persona and modeled inside generator profiles.
*   **Operator App Directory:** Renamed to `operator_app/` to avoid clashing with Python's stdlib `operator` module.
*   **Task Management:** Continue leveraging Taskmaster `.taskmaster/tasks/tasks.json` for the authoritative plan.
