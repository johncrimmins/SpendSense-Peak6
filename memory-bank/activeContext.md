# Active Context

## Current Focus
Implementation of Phase 1: Data & Logic.

## Recent History
*   Review of `project-brief.md`, `PRD.md`, and `architecture.md`.
*   Decision to include **htmx** in the tech stack for better UX.
*   Creation of Memory Bank (`memory-bank/`).
*   Initialization of Task Master project (though facing persistence issues, fallback to internal TODOs).
*   Defined granular tasks for Phase 1.
*   Completed baseline project scaffolding: directory tree, `requirements.txt`, and `.gitignore`.
*   Built deterministic synthetic data generator (`ingest/generator.py`) that outputs Plaid-style CSVs under `data/raw/`.
*   Added CSV loader (`ingest/loader.py`) to hydrate `spendsense.db` with normalized tables.

## Immediate Next Steps
1.  Execute **Task 4: Feature Engineering** (calculate behavioral metrics feeding personas).

## Active Decisions
*   **htmx Adoption:** Chosen to provide a responsive UI without the overhead of a full SPA framework (React/Vue) for the user-facing app.
*   **Persona "Optimizer":** Confirmed as the 5th persona.
*   **Task Management:** Using internal Todo list due to tool issues with Task Master persistence.
