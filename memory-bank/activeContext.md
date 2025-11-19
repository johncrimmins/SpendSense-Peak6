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

## Immediate Next Steps
1.  Execute **Task 2: Implement Data Generator**.
    *   Flesh out `ingest/generator.py` for 50–100 synthetic users.
    *   Ensure determinism and coverage of persona trigger metrics.
2.  Prep work for **Task 3: Data Loader**.
    *   Decide on SQLite schema scaffolding and shared constants.

## Active Decisions
*   **htmx Adoption:** Chosen to provide a responsive UI without the overhead of a full SPA framework (React/Vue) for the user-facing app.
*   **Persona "Optimizer":** Confirmed as the 5th persona.
*   **Task Management:** Using internal Todo list due to tool issues with Task Master persistence.
