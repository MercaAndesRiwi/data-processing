# ⚙️ MercaAndes Data Pipeline & Processing

Welcome to the unified **Data Processing & Simulation** repository for MercaAndes. This repository serves as the single source of truth for generating simulated data sources, consuming external APIs/streams, conducting exploratory data analysis (EDA), and normalizing datasets before loading them into the Silver/Gold layers.

---

## 🎯 Scope & Core Modules

This repository combines both source data provisioning and processing workflows:

1. **Database Simulation & Seeds (`simulators/`)**:
   * **POS Database (F2)**: Reproducible and idempotent database seeds for simulated point-of-sale transactions (`E-03`).
   * Parametric volume controls and configurable data quality flaws (e.g., negative prices, invalid SKUs) for testing pipeline robustness.

2. **Ingestion & Connectors (`src/ingestion/`)**:
   * **Historical Batch (F1)**: Loaders for Olist sales and logistics datasets.
   * **Inventory API Consumer (F3)**: REST client for periodic stock level polling.
   * **Marketplace Consumer (F4)**: Streaming and event capture for real-time order updates.

3. **Exploratory Data Analysis - EDA (`notebooks/`)**:
   * Data quality auditing, schema validation, duplicate checks, and distribution analysis for core sales metrics.

4. **Normalization & Cleansing (`src/processing/`)**:
   * PII Pseudonymization rules (`RN-11`).
   * Schema harmonization, timestamp alignment, and net sales calculation logic (`RN-01`).

---

## 📂 Project Structure

```text
data-processing/
├── data/
│   ├── raw/          # Raw ingested data (F1, F2, F3, F4)
│   ├── processed/    # Normalized and pseudonymized datasets
├── simulators/       # DB Seed scripts and mock data generators
│   ├── pos_seed.py   # Idempotent POS seed generator (E-03)
│   └── api_mock.py   # Local mock server for Inventory API (F3)
├── notebooks/        # Jupyter Notebooks for EDA and data profiling
│   ├── 01_pos_eda.ipynb
│   ├── 02_api_inspection.ipynb
│   └── 03_normalization_rules.ipynb
├── src/              # Reusable Python modules
│   ├── ingestion/    # API clients, batch loaders, and stream consumers
│   ├── processing/   # Cleansing, hashing (RN-11), and transformations
│   └── utils/        # Shared helpers and database connectors
├── tests/            # Unit & integration tests for seeds and pipelines
├── docker-compose.yml# Local setup for PostgreSQL, Mock API, and pipeline
├── README.md
└── requirements.txt