# MercaAndes Data Pipeline & Processing

Repository for the data-ingestion, simulation, exploration, and processing components of **MercaAndes Omnicanal**. The repository currently contains the POS sales simulator, ingestion scripts for exchange rates, public holidays, and weekly promotions, plus notebooks for inspecting the historical Olist dataset and POS data.

Some folders and modules are placeholders for future work. Their presence does not mean that the corresponding feature is implemented.

## Scope and implementation status

### Implemented components

- **POS sales simulator (F2 / HU-1.3):** generates reproducible point-of-sale sales and sale items for Colombia, Peru, Ecuador, Bolivia, and Chile. Supports `dev` and `full` modes, configurable seed and date range, links generated records to a run, and skips an already-registered run with the same country, period, and seed.
- **Exchange-rate ingestion:** retrieves historical USD exchange rates from the Frankfurter API and stores them in `public.exchange_rate`.
- **Holiday ingestion:** retrieves public holidays from the Nager.Date API for the five operational countries and stores them in `public.holidays`.
- **Promotion ingestion:** reads weekly Excel files from `data/raw/promotions/`, validates their columns and values, and inserts promotions into `public.promotions` while skipping duplicate records.
- **Exploratory analysis:** Jupyter notebooks inspect the Olist dataset and POS data.
- **Automated checks:** unit tests cover promotion-file validation; the integration test checks generated POS sale-item data against the PostgreSQL database.

### Planned or not yet implemented

- Inventory API simulator and consumer (F3).
- Marketplace order-event simulator and consumer (F4).
- General-purpose Silver/Gold transformations, PII pseudonymization (RN-11), and net-sales calculations (RN-01).
- The `src/processing/`, `src/utils/`, `database/migrations/`, and `database/seeds/` areas do not yet contain complete implementations.

## Project structure

```text
data-processing/
├── backups/                     
├── data/
│   ├── raw/
│   │   ├── catalog/              
│   │   └── promotions/           
│   └── processed/                
├── database/
│   ├── migrations/               
│   ├── schemas/pos/schema.sql    
│   └── seeds/                     
├── docs/
│   ├── adr/                      
│   ├── architecture/architecture.md
│   ├── backlog_sprint_1.md
│   └── bitacora/                  
├── infrastructure/docker/
│   └── docker-compose.yml         
├── notebooks/
│   ├── 01_kaggle_olist_inspection.ipynb
│   └── 02_pos_eda.ipynb
├── src/
│   ├── ingestion/
│   │   ├── exchange_rates/main.py
│   │   ├── holidays/main.py
│   │   └── promotions/main.py
│   ├── processing/                
│   ├── simulators/
│   │   ├── inventory_api/         
│   │   ├── marketplace_events/    
│   │   └── pos_seed/
│   │       ├── catalog.py
│   │       ├── config.py
│   │       ├── connection.py
│   │       ├── exchange_rates.py
│   │       ├── holidays.py
│   │       └── main.py
│   └── utils/                    
├── tests/
│   ├── integration/test_pos_seed.py
│   └── unit/test_promotions.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── uv.lock
└── README.md
```

## Requirements

- Python **3.13 or newer**, as declared in `pyproject.toml`.
- [`uv`](https://docs.astral.sh/uv/) for dependency and virtual-environment management.
- Docker Desktop or Docker Engine with Docker Compose, for the PostgreSQL service.
- Network access when loading exchange rates or holidays from external APIs.

## Local setup

Run these commands from the repository root in PowerShell or a terminal.

### 1. Install Python dependencies

```powershell
uv sync --locked
```

Verify the environment and tools:

```powershell
uv run python --version
uv run pytest --version
uv run ruff --version
```

### 2. Configure environment variables

Create a local `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Set the PostgreSQL connection values in `.env`. The example values are placeholders; replace `change_me` values with the credentials configured for your local database. Do not commit `.env` or real credentials.

The POS generator uses these variables:

| Variable                       | Purpose                                                | Example/default               |
| ------------------------------ | ------------------------------------------------------ | ----------------------------- |
| `POS_DB_HOST`                | PostgreSQL host                                        | `localhost`                 |
| `POS_DB_PORT`                | Published PostgreSQL port                              | `5432`                      |
| `POS_DB_NAME`                | Database name                                          | Configure locally             |
| `POS_DB_USER`                | Database user                                          | Configure locally             |
| `POS_DB_PASSWORD`            | Database password                                      | Configure locally             |
| `POS_SEED`                   | Seed for repeatable generation                         | `42`                        |
| `POS_MODE`                   | Generation mode:`dev` or `full`                    | `dev`                       |
| `POS_DEV_SALES_PER_COUNTRY`  | Sales per country in dev mode                          | `100`                       |
| `POS_FULL_SALES_PER_COUNTRY` | Sales per country in full mode                         | `400000`                    |
| `POS_PRICE_DEFECT_RATE`      | Artificial invalid-price rate for data-quality testing | `0.005`                     |
| `POS_SKU_DEFECT_RATE`        | Artificial SKU-defect rate for data-quality testing    | `0.01`                      |
| `POS_START_DATE`             | First date in the generation period                    | Configure the required period |
| `POS_END_DATE`               | Last date in the generation period                     | Configure the required period |

Make sure `POS_START_DATE` and `POS_END_DATE` cover the period you intend to generate. The supplied promotion files are from 2026, so use a matching period when validating those promotions.

### 3. Start PostgreSQL

```powershell
docker compose -f infrastructure/docker/docker-compose.yml up -d
```

The Compose service uses PostgreSQL 16 and persists data in the `pos_data` Docker volume. The `database/schemas/pos/schema.sql` initialization script is automatically applied only when PostgreSQL initializes a **new, empty** data volume. If the volume already exists, changing the SQL file will not automatically recreate the database.

The POS generator expects country schemas and catalog data to be present before generation. The schema script creates the POS tables, but catalog loading must be handled separately with the available project data/process agreed by the team.

## Running ingestion and simulation

Run commands from the repository root.

### Load exchange rates

```powershell
uv run python -m src.ingestion.exchange_rates.main
```

This retrieves historical USD exchange rates for the currencies used by the operational countries and writes them to `public.exchange_rate`.

### Load public holidays

```powershell
uv run python -m src.ingestion.holidays.main
```

The current script requests holidays for 2026 for Colombia, Peru, Ecuador, Bolivia, and Chile, and writes them to `public.holidays`.

### Load weekly promotions

Place the weekly promotion `.xlsx` files in `data/raw/promotions/`, then run:

```powershell
uv run python -m src.ingestion.promotions.main
```

The workbook must use these exact columns: `sku`, `tienda_o_canal`, `descuento_pct`, `fecha_inicio`, and `fecha_fin`. The script validates records and skips promotion records that already exist in the database.

### Generate POS sales

First confirm that the database has the required country schemas, branches, products, exchange rates, holidays, and promotions for the configured date range. Then run:

```powershell
uv run python -m src.simulators.pos_seed.main
```

The generator supports these operational country schemas:

| Country code | PostgreSQL schema | Currency |
| ------------ | ----------------- | -------- |
| `CO`       | `colombia`      | COP      |
| `PE`       | `peru`          | PEN      |
| `EC`       | `ecuador`       | USD      |
| `BO`       | `bolivia`       | BOB      |
| `CL`       | `chile`         | CLP      |

In `dev` mode, the default is 100 sales per country. In `full` mode, the default is 400,000 sales per country (2,000,000 across the five countries). Set `POS_MODE` and the relevant sales-count variables in `.env` before running. A completed run with the same country, date range, and seed is skipped to avoid duplicate batches; changing configuration alone will not regenerate that existing batch.

The simulator adjusts date selection to favor weekends, public holidays, and promotion dates. It applies the highest matching active promotion for supported digital channels (`E-commerce Propio` and `Marketplace Propietario`). Physical-store promotion matching is not applied by the current generator.

## Tests and code quality

Run unit tests:

```powershell
uv run pytest tests/unit
```

Run the POS integration test:

```powershell
uv run pytest tests/integration
```

The integration test requires a reachable PostgreSQL database containing the expected schemas and test data. Its current assertion expects 100 sale-item records per country, so run it against the corresponding development dataset rather than the full annual dataset.

Run all tests:

```powershell
uv run pytest
```

Check code style:

```powershell
uv run ruff check
```

Launch JupyterLab:

```powershell
uv run jupyter lab
```

## Dependency management

- `pyproject.toml` declares project dependencies and development tools.
- `uv.lock` records resolved versions for reproducible environment setup.
- `requirements.txt` is retained temporarily while the team checks whether any workflow still depends on it. Use `uv` for new dependency changes.

Add a runtime dependency:

```powershell
uv add package-name
```

Add a development dependency:

```powershell
uv add --dev package-name
```

Commit `pyproject.toml` and `uv.lock` together after dependency changes.

## Data, backups, and secrets

- Keep `.env`, database dumps, local credentials, and other secrets out of version control.
- `backups/` is for local recovery files; store backups securely and do not commit them to the repository.
- Treat `data/raw/` files as source inputs. Only keep source workbooks in version control if the team has permission to share them and they are required by the project.
- The `.venv/`, Python cache files, notebook checkpoints, and local editor settings should not be committed.

## Collaboration

- Work on dedicated branches and review changes before merging into the shared development branch.
- Preserve notebooks and teammates' implementations; coordinate before replacing shared files.
- Update this README when a component's implementation or execution procedure change


# MercaAndes Data Pipeline & Processing

Welcome to the **MercaAndes Data** **Processing** **& Simulation** repository. This repository organizes simulated data source generation, external data ingestion, exploratory data analysis (EDA), and data transformation workflows to support the integration of data into the Silver and Gold layers.

---

## Scope & Core Modules

This repository covers four main areas:

### 1. Database Simulation & Data Generation

- **POS Database (F2):** Reproducible generation of simulated point-of-sale data by country.
- **Inventory API (F3):** Preparation and development of inventory simulation and API consumption components.
- **Marketplace Events (F4):** Preparation of components for capturing marketplace order events.
- Generation of test data to evaluate data quality and pipeline robustness.

### 2. Ingestion & Connectors

- **Historical Batch (F1):** Ingestion of the Olist historical dataset.
- **Inventory API Consumer (F3):** REST client for retrieving inventory data.
- **Marketplace Consumer (F4):** Components for capturing and processing order events.

### 3. Exploratory Data Analysis (EDA)

Jupyter notebooks will be used to inspect source datasets, assess data quality, identify duplicates, validate schemas, and analyze relevant distributions and metrics.

### 4. Data Processing & Normalization

Planned processing capabilities include:

- Data cleaning and validation.
- Schema harmonization and timestamp alignment.
- Personally identifiable information (PII) pseudonymization (RN-11).
- Net sales calculations according to the project's business rules (RN-01).

These capabilities describe the intended scope. Each component will be implemented and tested incrementally.

---

## Project Structure

```text
data-processing/
├── config/
├── backups/
│   └── mercaandes_backup.dump
|
├── data/
│   ├── raw/
|   |   ├── catalog/
|   |   |   └──MercaAndes_catalogo_Marketplace_Completo.xlsx
|   |   └──promotions/
│   │   |	├── promociones_2026-41.xlsx
│   │   |	├── promociones_2026-42.xlsx
│   │   |	└── promociones_2026-43.xlsx
│   └── processed/
├── database/
│   ├── migrations/
│   ├── schemas/
│   │   └── pos/
│   │   |	└── schema.sql
│   └── seeds/
├── docs/
│   ├── adr/
│   │   └──ADR-001-estructura-base-y-convenciones.md
│   ├── architecture/
│   │   └── architecture.md
|   ├──bitacora/
|   |  └──2026-10-02-inspeccion-dataset-kaggle-olist.md
│   └── baclog_sprint_1.md
├── infrastructure/
│   └── docker/
|   |   └──docker-compose.yml
├── notebooks/
│   ├── 01_kaggle_olist_inspection.ipynb
│   └── 02_pos_eda.ipynb
├── src/
│   ├── ingestion/
│   │   ├── exchanges_rate/
|   |   |   └──main.py
│   │   ├── holidays/
│   │   └── promotions/
|   |   |   └──main.py
│   ├── processing/
│   ├── simulators/
│   │   ├── inventory_api/
│   │   ├── marketplace_events/
│   │   └── pos_seed/
|   |   |   ├──catalog.py
|   |   |   ├──config.py
|   |   |   ├──connection.py
|   |   |   ├──exchange_rates.py
|   |   |   ├──holidays.py
|   |   |   └──main.py
│   └── utils/
├── tests/
│   ├── integration/
|   |   |   └──test_pos_seed.py
│   └── unit/
|   |   |   └──test_promotions.py
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── uv.lock
└── README.md
```

Empty directories are placeholders for future components. Their presence does not imply that the corresponding functionality has already been implemented.

---

## Prerequisites

- Python 3.13 or a compatible version supported by `pyproject.toml`.
- [uv](https://docs.astral.sh/uv/) for Python dependency and virtual environment management.
- Git for version control.

Docker will be used when containerized services are introduced.

---

## Local Development Setup

From the repository root, run:

```powershell
uv sync --locked
```

This synchronizes the local environment with the dependencies declared in `pyproject.toml` and the versions recorded in `uv.lock`.

Verify the environment:

```powershell
uv run python --version
uv run pytest --version
uv run ruff --version
```

To launch JupyterLab:

```powershell
uv run jupyter lab
```

The `.venv/` directory is managed locally and must not be committed to Git.

---

## Configuration & Local Data

The `.env.example` file documents example environment variables. When a component requires local configuration, create a `.env` file containing the appropriate values.

Never commit real passwords, access tokens, or other secrets.

---

## Testing & Code Quality

Run the available tests:

```powershell
uv run pytest
```

Check Python code quality:

```powershell
uv run ruff check
```

---

## Dependency Management

- `pyproject.toml` declares the project's direct dependencies and development tools.
- `uv.lock` records the resolved dependency versions to support reproducible environments.
- `requirements.txt` is retained temporarily while the team reviews its removal and checks for any remaining dependencies on that file.

Use `uv` for new dependency changes. For example:

```powershell
uv add package-name
```

For development-only tools:

```powershell
uv add --dev package-name
```

After changing dependencies, commit the updated `pyproject.toml` and `uv.lock` together.

---

## Collaboration Guidelines

- Work on dedicated branches and review changes before merging them into the shared development branch.
- Preserve existing notebooks and teammates' implementations.
- Avoid overwriting shared files without coordinating with their owners.
- Update this README as components are implemented and validate
