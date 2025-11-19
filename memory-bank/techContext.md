# Tech Context

## Technology Stack

### Backend
*   **Language:** Python 3.11+
*   **Framework:** FastAPI
*   **Database:** SQLite
*   **ORM:** SQLAlchemy (Async)
*   **Data Processing:** Pandas

### Frontend (User App)
*   **Templating:** Jinja2
*   **Styling:** TailwindCSS
*   **Interactivity:** htmx (Hypertext Markup Extensions)
*   **Charts:** Chart.js

### Frontend (Operator App)
*   **Framework:** Streamlit

### Development Tools
*   **Package Manager:** `pip` (requirements.txt)
*   **Linting:** `ruff` or `flake8` (standard Python tooling)
*   **Testing:** `pytest`

## Setup Requirements
*   **Local Environment:** Standard Python environment.
*   **Dependencies:** defined in `requirements.txt`.
*   **No External APIs:** System runs entirely offline with synthetic data.

## Constraints
*   **Performance:** Recommendations generation < 5 seconds per user.
*   **Browser:** Modern browser support for CSS Grid/Flexbox and gradients.

