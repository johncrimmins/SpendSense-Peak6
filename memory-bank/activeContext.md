# Active Context

## Current Focus
Implementation of Phase 1: Data & Logic.

## Recent History
*   Review of `project-brief.md`, `PRD.md`, and `architecture.md`.
*   Decision to include **htmx** in the tech stack for better UX.
*   Creation of Memory Bank (`memory-bank/`).
*   Initialization of Task Master project (though facing persistence issues, fallback to internal TODOs).
*   Defined granular tasks for Phase 1.
*   Completed Task 1 by standing up the repo structure, requirements, and .gitignore baseline.
*   Finished Task 2 with a deterministic `ingest/generator.py` that exports persona-rich CSVs plus a CLI runner.
*   Completed Task 3 by wiring `ingest/loader.py` to build the SQLite schema and ingest the CSVs idempotently.

## Immediate Next Steps
1.  Execute **Task 4: Feature Engineering**.
    *   Implement `engine/features.py` to calculate burn rate, runway, and inefficiency using the SQLite data.
    *   Persist results to a `financial_snapshot` table for API consumption.
2.  Execute **Task 5: Persona Classifier**.
    *   Derive deterministic persona assignment from the computed features and store results on each user record.

## Active Decisions
*   **htmx Adoption:** Chosen to provide a responsive UI without the overhead of a full SPA framework (React/Vue) for the user-facing app.
*   **Persona "Optimizer":** Confirmed as the 5th persona.
*   **Task Management:** Using internal Todo list due to tool issues with Task Master persistence.
