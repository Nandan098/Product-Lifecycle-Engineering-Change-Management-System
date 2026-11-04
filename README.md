# Product Lifecycle & Engineering Change Management System

**Portfolio project aligned to Capgemini SAP Manufacturing: SAP PLM + PLM System Integration (PLMSI).**

This is a runnable educational application that simulates product lifecycle and engineering-to-manufacturing workflows. It is not an SAP installation or a certified connector to Teamcenter or another licensed PLM product.

## What the application demonstrates

- Product master and revision history.
- Engineering Bill of Materials (EBOM) and Manufacturing Bill of Materials (MBOM).
- Controlled documents and revision review flags.
- Engineering Change Request (ECR) submission, review and rejection.
- Engineering Change Order (ECO) approval and implementation.
- Change impact analysis across BOM usage, documents and open production orders.
- EBOM-to-MBOM transformation using component-to-operation mappings.
- External PLM data exchange simulation using REST endpoints and JSON payloads.
- Integration job monitoring, validation and error records.
- CSV exports for a Power BI report.

## Technology stack

- Python 3.10+
- Streamlit (web application)
- FastAPI + Uvicorn (REST integration API)
- SQLite (default local database)
- Pandas + Plotly (tables and visualizations)
- Pytest + HTTPX (automated tests)

## Quick start — Windows

1. Extract the ZIP and open the project folder in VS Code.
2. Open a terminal in the project folder.
3. Run:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m scripts.init_database
streamlit run app.py
```

The app opens at `http://localhost:8501`. It creates `data/plm_demo.db` and loads sample data on first run. The seed script does not overwrite an existing database.

Alternatively, double-click `run_windows.bat` after installing Python. The script creates a virtual environment if needed and starts Streamlit.

## Quick start — macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.init_database
streamlit run app.py
```

## Start the REST API

Open a second terminal in the project folder, activate the same virtual environment, then run:

```bash
python -m scripts.run_api
```

- API health: `http://127.0.0.1:8000/health`
- Interactive OpenAPI docs: `http://127.0.0.1:8000/docs`
- Product API: `GET /api/v1/products`
- EBOM API: `GET /api/v1/products/{product_id}/ebom`
- MBOM API: `GET /api/v1/products/{product_id}/mbom`
- External EBOM import: `POST /api/v1/integrations/ebom/import`
- External ECR import: `POST /api/v1/integrations/ecr/import`
- EBOM-to-MBOM sync: `POST /api/v1/products/{product_id}/sync-mbom`
- Integration jobs: `GET /api/v1/integration-jobs`

The sample payload at `data/external_ebom_revision_B.json` can be uploaded in the Integration Center or posted to the API. It represents an **already approved** external revision; the importer rejects drafts and validates all component material numbers.

## Suggested demo walkthrough

### Flow A — internal engineering change

1. Open **Product & EBOM** and inspect `GEAR-ASSY-100`, revision A.
2. Open **Change Impact Analysis** and analyze `BRG-6205` to see affected BOM usage, controlled documents and open production orders.
3. Open **Engineering Change Control** and submit an ECR replacing `BRG-6205` with `BRG-6205-2RS` (quantity 2).
4. Start review, approve the ECR to create an ECO, then implement the ECO.
5. The system creates EBOM revision B and flags revision-A documents as `REVIEW_REQUIRED`.
6. Open **PLM Integration Center** and synchronize revision B to MBOM.
7. Inspect the updated MBOM and integration job record.

### Flow B — external PLM integration

1. Reset your demo database only if you want a clean baseline (see Reset section below).
2. Open **PLM Integration Center**.
3. Use the included `external_ebom_revision_B.json` payload and select **Import approved EBOM**.
4. The integration job records source system, payload type, row count, status and validation message.
5. Synchronize the imported EBOM to MBOM.

## Reset demo data

Stop Streamlit and the API. Delete `data/plm_demo.db` (and its `-wal` / `-shm` files if present), then run:

```bash
python -m scripts.init_database
```

Never delete the database while the app or API is running.

## Tests

```bash
pytest -q
```

The tests cover seeded product structures, change impact analysis, ECR/ECO lifecycle, revision creation, MBOM transformation, external EBOM validation and REST API endpoints.

## Power BI exports

Use the **Power BI Exports** page or run:

```bash
python -m scripts.export_powerbi
```

CSV files are written to `exports/`. Suggested Power BI pages:

1. Product and Revision Overview.
2. Engineering Change Pipeline (ECR/ECO status and aging).
3. EBOM vs MBOM structure and component mapping.
4. Integration Job Monitor (success/failure, source, payload type).
5. Open Production Order Impact.

Suggested relationships: `products.product_id` to EBOM/MBOM/documents/orders; `engineering_changes.ecr_id` to `change_orders.ecr_id`; use `job_id` as the integration-job row key.

## Database location

By default: `data/plm_demo.db`.

To use another path, set `PLM_DB_PATH` before running the application/API. Relative paths resolve from this project directory. See `.env.example` for the setting. The app does not automatically load `.env`; export the variable in your terminal or use your preferred environment-variable loader.

## Project structure

```text
Product_Lifecycle_Engineering_Change_Management/
├── app.py
├── api/                 # FastAPI endpoints
├── core/                # Database, schema, configuration and demo seed
├── services/            # Change, impact, integration, product and analytics logic
├── data/                # Example external PLM JSON payloads
├── docs/                # FRD, process flow, test plan, data dictionary and interview guide
├── tests/               # Automated backend and API tests
├── scripts/             # Database setup, API runner and CSV exports
├── exports/             # Power BI CSV output location
├── requirements.txt
└── README.md
```

## Important scope and honesty notes

- SAP PP / PEO / PLM / PLMSI are represented as **business-process concepts**; this project does not configure or connect to an SAP system.
- The external engineering source is named `Teamcenter-Sim` and uses example JSON payloads. No live Siemens Teamcenter, SAP PLM or SAP PLMSI connection is included.
- ECR/ECO approval is simplified for a student demo; real consulting deployments need role-based authorization, audit controls and formal release strategies.
- The included database is SQLite for portability. A production solution would use an enterprise database and hardened application architecture.
- The sample engineering documents are metadata placeholders, not actual CAD/PDF drawings.

## Suggested resume wording after you implement and verify the features

**Product Lifecycle & Engineering Change Management System | Python, FastAPI, SQLite, Streamlit, REST APIs, JSON**

- Developed a product lifecycle application to manage product structures, EBOM revisions and controlled engineering documents.
- Implemented ECR/ECO approval workflows with revision control, effective dates and traceable change history.
- Built change-impact analysis to identify affected components, manufacturing BOMs, documents and open production orders.
- Developed REST/JSON integration endpoints to validate external PLM payloads and synchronize approved EBOM data into manufacturing BOM structures.

Only claim these bullets once you have run and understood the corresponding features.
