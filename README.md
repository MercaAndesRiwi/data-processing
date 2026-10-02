# ⚙️ MercaAndes Data Processing

Welcome to the **Data Processing** repository for the MercaAndes project. This repository handles the core data engineering steps prior to dimensional modeling and analytics: **data collection (ingestion), exploratory data analysis (EDA), and data normalization/cleaning**.

---

## 🎯 Objective

Transform heterogeneous and fragmented business data sources (F1 Olist, F2 POS, F3 Inventory API, and F4 Marketplace Streaming) into clean, standardized, pseudonymized, and validated datasets aligned with MercaAndes business rules.

---

## 📌 Scope & Modules

1. **Data Collection & Ingestion (`ingestion/`)**:
   * Batch processing for historical datasets (CSV / Parquet).
   * API consumers and scripts for real-time/scheduled inventory checks.
   * Event consumer and stream capture.

2. **Exploratory Data Analysis - EDA (`notebooks/`)**:
   * Data quality auditing, null value detection, duplicate checks, and anomaly detection (e.g., price $\le 0$ or invalid SKUs).
   * Statistical distribution analysis for core metrics (gross sales, returns, stock velocity).

3. **Normalization & Data Cleansing (`processing/`)**:
   * Schema harmonization, data type casting, and timestamp standardization.
   * Implementation of PII pseudonymization rules (`RN-11`).
   * Controlled cleaning and imputation to populate the Data Lake / Silver Layer.

---

## 📂 Project Structure

```text
data-processing/
├── data/
│   ├── raw/          # Raw collected data (F1, F2, F3, F4)
│   ├── processed/    # Cleaned, normalized, and pseudonymized datasets
├── notebooks/        # Jupyter Notebooks for EDA and hypothesis testing
│   ├── 01_ingestion_check.ipynb
│   ├── 02_eda_exploration.ipynb
│   └── 03_normalization_rules.ipynb
├── src/              # Reusable Python modules
│   ├── ingestion/    # Connection and ingestion scripts
│   ├── cleaning/     # Transformation and normalization functions
│   └── utils/        # General utilities and validation helpers
├── tests/            # Unit tests for data quality and transformation logic
├── .gitignore
├── README.md
└── requirements.txt
```
