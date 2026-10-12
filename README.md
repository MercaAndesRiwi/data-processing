
# MercaAndes Data Pipeline & Processing

Repository for the data-ingestion, simulation, exploration, and processing components of **MercaAndes Omnicanal**. The repository currently contains the POS sales simulator, ingestion scripts for exchange rates, public holidays, and weekly promotions, plus notebooks for inspecting the historical Olist dataset and POS data.

Some folders and modules are placeholders for future work. Their presence does not mean that the corresponding feature is implemented.

## Scope and implementation status

### Implemented components

- **Seeded master catalog (`src/common/master_catalog.py`):** deterministic products, sellers and stores from `MASTER_SEED` (default 71 x 15 = 1065 products, 35 sellers, 20 stores). Single ID space shared by POS (F2), inventory (F3) and marketplace events (F4). Replaces the gitignored Excel workbook, which is no longer required.
- **POS sales simulator (F2 / HU-1.3):** generates reproducible point-of-sale sales and sale items for Colombia, Peru, Ecuador, Bolivia, and Chile. Supports `dev` and `full` modes, configurable seed and date range, links generated records to a run, and skips an already-registered run with the same country, period, and seed. Product data comes from the seeded catalog.
- **Marketplace event producer (F4):** seeded order lifecycle `created -> paid -> shipped -> delivered / cancelled / returned` with the post-dispatch rule (cancel from shipped yields returned), configurable duplicate injection by `event_id` and out-of-order delivery capped at 6 hours. Peak mode exceeds 20 events/second; see `docs/bitacora/2026-10-12-throughput-marketplace.md`.
- **Inventory helper and catalog-backed API (F3):** deterministic `stock_level(seed, sku, store_id)` from the shared catalog. `api_seller.py` preserves the original mock API; `catalog_api.py` is an additional catalog-backed API that returns shared SKU, store, and seller IDs. `consumer.py` can poll the catalog-backed API.
- **Database migrations (Alembic):** `database/migrations/versions/0001_baseline.py` freezes the current `schema.sql`. Structure is versioned with `alembic upgrade head`; seeds always run afterwards and never delete data.
- **Exchange-rate ingestion:** retrieves historical USD exchange rates from the Frankfurter API and stores them in `public.exchange_rate`.
- **Holiday ingestion:** retrieves public holidays from the Nager.Date API for the five operational countries and stores them in `public.holidays`.
- **Promotion ingestion:** reads weekly Excel files from `data/raw/promotions/`, validates their columns and values, and inserts promotions into `public.promotions` while skipping duplicate records.
- **Exploratory analysis:** Jupyter notebooks inspect the Olist dataset and POS data.
- **Automated checks:** unit tests cover promotion-file validation; the integration test checks generated POS sale-item data against the PostgreSQL database.

### Planned or not yet implemented

- End-to-end operational integration of the original mock F3 API with the shared catalog. The original API intentionally retains its independent mock SKU and seller IDs; use the catalog-backed API for shared-ID inventory.
- Marketplace Kafka consumer with watermark 6h and `MERGE` on `order_id`.
- General-purpose Silver/Gold transformations, PII pseudonymization (RN-11), and net-sales calculations (RN-01).
- The `src/processing/`, `src/utils/`, `database/migrations/`, and `database/seeds/` areas do not yet contain complete implementations.

## Project structure

```text
data-processing/                
├── data/
│   ├── raw/
│   │   ├── catalog/           
│   │   └── promotions/       
│   └── processed/             
├── database/
│   ├── migrations/                  # Alembic env + versions (0001_baseline)
│   ├── schemas/pos/schema.sql       # Frozen baseline source for 0001
│   └── seeds/                       # Placeholder for database seed scripts
├── docs/
│   ├── adr/                  
│   ├── architecture/architecture.md
│   ├── backlog_sprint_1.md
│   └── bitacora/                    # Project investigation notes
│       └── 2026-10-12-throughput-marketplace.md
├── infrastructure/docker/
│   └── docker-compose.yml   
├── notebooks/
│   ├── 01_kaggle_olist_inspection.ipynb
│   └── 02_pos_eda.ipynb
├── src/
│   ├── common/
│   │   ├── config.py                # MASTER_SEED, countries, catalog sizing
│   │   ├── db.py                    # Single SQLAlchemy engine factory
│   │   └── master_catalog.py        # Seeded products/sellers/stores
│   ├── ingestion/
│   │   ├── exchange_rates/main.py
│   │   ├── holidays/main.py
│   │   ├── inventory/                # consumer.py, adapter.py
│   │   └── promotions/main.py
│   ├── processing/          
│   ├── simulators/
│   │   ├── inventory_api/           # api_seller.py, catalog_api.py, stock.py
│   │   ├── marketplace_events/      # lifecycle.py, faults.py, producer.py
│   │   └── pos_seed/
│   │       ├── catalog.py           # Loads DB catalog from seeded data
│   │       ├── config.py
│   │       ├── connection.py
│   │       ├── exchange_rates.py
│   │       └── main.py
│   └── utils/              
├── tests/
│   ├── integration/test_pos_seed.py
│   └── unit/                        # 21 tests: promotions, catalog,
│                                    # lifecycle, faults, throughput, inventory
├── alembic.ini
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
| `MASTER_SEED`                | Shared seed for catalog, POS, inventory, events        | `42`                        |
| `CATALOG_PER_CATEGORY`       | Products per category (71 x N)                         | `15`                        |
| `CATALOG_ACTIVE_RATE`        | Fraction of catalog marked Activo                      | `0.95`                      |
| `INVENTORY_API_URL`          | Base URL used by the F3 consumer                       | `http://127.0.0.1:8001`     |
| `INVENTORY_API_TOKEN`        | Bearer token used by the F3 consumer                   | `token-seller-123`          |
| `INVENTORY_SELLER_ID`        | Catalog seller requested by the consumer               | `SEL-PRV-001`               |
| `ERROR_RATE`                 | Simulated 429/503 error probability for F3 APIs        | `0.03`                      |
| `ENABLE_NEGATIVE_INVENTORY`  | Enables negative stock simulation                      | `true`                      |
| `F4_DUPLICATE_RATE`          | Duplicate-event injection rate                         | `0.0`                       |
| `F4_OOO_ENABLED`             | Out-of-order delivery toggle                           | `false`                     |
| `F4_OOO_MAX_LAG_SEC`         | Max arrival lag seconds (cap 21600 = 6h)               | `21600`                     |

Make sure `POS_START_DATE` and `POS_END_DATE` cover the period you intend to generate. The supplied promotion files are from 2026, so use a matching period when validating those promotions.

### 3. Start PostgreSQL (once)

```powershell
docker compose --env-file .env -f infrastructure/docker/docker-compose.yml up -d
uv run python -m src.simulators.pos_seed.connection
```

The Compose service uses PostgreSQL 16 and persists data in the `pos_data` Docker volume. The init script applies only on a **new, empty** volume; day to day, structure is managed with `alembic upgrade head` (no data loss).

## Execution step by step

From the repository root, in this order. Seeds never delete data.

```powershell
uv run alembic upgrade head
uv run python -m src.ingestion.exchange_rates.main
uv run python -m src.ingestion.holidays.main
uv run python -m src.ingestion.promotions.main
uv run python -m src.simulators.pos_seed.catalog
uv run python -m src.simulators.pos_seed.main
uv run python -m src.simulators.marketplace_events.producer --orders 100
uv run pytest tests/unit
```

### What each step does (no extra commands)

1. **Structure without data loss:** versioned migrations (`0001_baseline`
   freezes `schema.sql`). Check with `alembic current` (`0001 (head)`).
   New tables go in `0002_*`, never editing `schema.sql` by hand.
2. **Exchange rates:** fills `public.exchange_rate`. Required before POS.
3. **Holidays:** fills `public.holidays` 2026 (5 countries) for seasonality.
4. **Promotions:** place `.xlsx` in `data/raw/promotions/` first. Columns
   `sku, tienda_o_canal, descuento_pct, fecha_inicio, fecha_fin`.
   Skips existing records.
5. **Catalog:** builds products from `MASTER_SEED`, upserts categories and
   active products per country. Idempotent via `ON CONFLICT (sku)`.
6. **POS sales:** needs schemas, branches, products, rates, holidays and
   promos for the configured period. Skips completed
   (country, period, seed) runs. `dev` 100/country, `full` 400k/country.
7. **Marketplace events (no DB):** IDs from the same seeded catalog.
   Faults via flags in the order block (`--duplicate-rate`, `--ooo`).
   Evidence: `docs/bitacora/2026-10-12-throughput-marketplace.md`.

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

## F3 inventory APIs and consumer

F3 currently has two API entry points. They serve different purposes and must not be confused:

- `api_seller.py` is the original teammate implementation. It returns mock IDs such as `SKU-00094` and `SELLER_001`. Keep it unchanged for its original mock API tests.
- `catalog_api.py` is the additional catalog-backed API. It uses `build_master_catalog()` and `stock_level()` and returns IDs from the shared catalog. Use this API when validating compatibility with F2 and F4.

Start each service from the repository root in a separate PowerShell terminal.

**Terminal 1 — original F3 mock API (port 8000):**

```powershell
uv run uvicorn src.simulators.inventory_api.api_seller:app --reload --host 127.0.0.1 --port 8000
```

Swagger: `http://127.0.0.1:8000/docs`

**Terminal 2 — catalog-backed F3 API (port 8001):**

```powershell
uv run uvicorn src.simulators.inventory_api.catalog_api:app --reload --host 127.0.0.1 --port 8001
```

Swagger: `http://127.0.0.1:8001/docs`

Use a seller ID from the shared catalog, such as `SEL-PRV-001`, with the catalog-backed API. Authorize with the local test token `token-seller-123`. The original mock API uses its own mock seller IDs; those IDs are not automatically mapped to the shared catalog.

**Terminal 3 — consume the catalog-backed API:**

Set these local `.env` values (do not commit `.env`):

```env
INVENTORY_API_URL=http://127.0.0.1:8001
INVENTORY_API_TOKEN=token-seller-123
INVENTORY_SELLER_ID=SEL-PRV-001
ERROR_RATE=0.03
ENABLE_NEGATIVE_INVENTORY=true
```

Then run:

```powershell
uv run python -m src.ingestion.inventory.consumer
```

The consumer reports unknown SKU IDs, whether the seller exists in the catalog, negative quantities, and missing `store_id` fields. Because `ERROR_RATE` may simulate HTTP 429 or 503 responses, a request can fail intermittently. The consumer retries those statuses.

The standalone `adapter.py` builds catalog-compatible inventory records directly from the shared catalog and `stock.py`; it does not call either HTTP API or write to PostgreSQL. Run its tests with:

```powershell
uv run pytest tests/integration/test_inventory_adapter.py -v
uv run pytest tests/unit/test_inventory.py -v
```

**Current integration boundary:** the original mock API and catalog-backed API remain separate. This preserves the teammate's original implementation while providing a catalog-compatible path for F2/F4 integration. Do not claim that the original mock IDs are mapped to catalog IDs; no such mapping exists.

---

## Tests and code quality

Run unit tests (21 tests: promotions, master catalog, lifecycle, faults, throughput, inventory):

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
- Update this README when a component's implementation or execution procedure changes.
