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
│   ├── environments/
│   └── schemas/
├── data/
│   ├── raw/
│   └── processed/
├── database/
│   ├── migrations/
│   ├── schemas/
│   └── seeds/
├── infrastructure/
│   └── docker/
├── notebooks/
├── scripts/
├── src/
│   ├── ingestion/
│   ├── processing/
│   ├── simulators/
│   │   ├── inventory_api/
│   │   ├── marketplace_events/
│   │   └── pos_seed/
│   └── utils/
├── tests/
│   ├── integration/
│   └── unit/
├── .env.example
├── .gitignore
├── .dockerignore
├── pyproject.toml
├── requirements.txt
├── uv.lock
├── Dockerfile
├── docker-compose.yml
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
