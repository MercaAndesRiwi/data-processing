-- Create one POS schema for each operational country
CREATE SCHEMA IF NOT EXISTS colombia;
CREATE SCHEMA IF NOT EXISTS peru;
CREATE SCHEMA IF NOT EXISTS ecuador;
CREATE SCHEMA IF NOT EXISTS bolivia;
CREATE SCHEMA IF NOT EXISTS chile;


-- POS tables for each country

DO $$
DECLARE
    country_schema TEXT;
BEGIN
    FOREACH country_schema IN ARRAY ARRAY[
        'colombia',
        'peru',
        'ecuador',
        'bolivia',
        'chile'
    ]
    LOOP

        -- Branches
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I.branch (
                branch_id BIGINT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                branch_zip_code VARCHAR(20),
                city VARCHAR(100) NOT NULL,
                state VARCHAR(100) NOT NULL
            )', country_schema);

        -- Product categories
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I.product_category (
                product_category_id INTEGER PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE
            )', country_schema);

        -- Products
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I.product (
                product_id VARCHAR(50) PRIMARY KEY,
                product_category_id INTEGER NOT NULL,
                sku VARCHAR(50) NOT NULL UNIQUE,
                name VARCHAR(150) NOT NULL,
                base_price_usd NUMERIC(12, 2),

                CONSTRAINT fk_product_category
                    FOREIGN KEY (product_category_id)
                    REFERENCES %I.product_category(product_category_id)
            )', country_schema, country_schema);

        -- Sales
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I.sale (
                sale_id BIGINT PRIMARY KEY,
                sale_at TIMESTAMP NOT NULL,
                branch_id BIGINT NOT NULL,
                payment_method VARCHAR(50) NOT NULL,
                currency_code VARCHAR(3) NOT NULL DEFAULT 'USD',

                CONSTRAINT fk_sale_branch
                    FOREIGN KEY (branch_id)
                    REFERENCES %I.branch(branch_id)
            )', country_schema, country_schema);

        -- Sales line items
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I.sale_item (
                sale_item_id BIGINT PRIMARY KEY,
                sale_id BIGINT NOT NULL,
                product_id VARCHAR(50) NOT NULL,
                sku VARCHAR(50) NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price NUMERIC(12,2) NOT NULL,

                CONSTRAINT fk_sale_item_sale
                    FOREIGN KEY (sale_id)
                    REFERENCES %I.sale(sale_id),

                CONSTRAINT fk_sale_item_product
                    FOREIGN KEY (product_id)
                    REFERENCES %I.product(product_id),

                CONSTRAINT chk_sale_item_quantity
                    CHECK (quantity > 0)
            )', country_schema, country_schema, country_schema);

    END LOOP;
END $$;


-- Weekly promotions ingestion destination

CREATE TABLE IF NOT EXISTS public.promotions (
    promotion_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sku VARCHAR(50) NOT NULL,
    store_or_channel VARCHAR(100) NOT NULL,
    discount_pct NUMERIC(5,2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    CONSTRAINT chk_promotions_discount
        CHECK (discount_pct > 0 AND discount_pct <= 100),

    CONSTRAINT chk_promotions_dates
        CHECK (end_date >= start_date)
);


CREATE TABLE IF NOT EXISTS public.exchange_rate (
    rate_date DATE NOT NULL,
    base_currency_code VARCHAR(3) NOT NULL,
    quote_currency_code VARCHAR(3) NOT NULL,
    rate NUMERIC(18, 8) NOT NULL CHECK (rate > 0),
    source VARCHAR(50) NOT NULL DEFAULT 'Frankfurter',
    PRIMARY KEY (
        rate_date,
        base_currency_code,
        quote_currency_code
    )
);


CREATE TABLE IF NOT EXISTS public.pos_seed_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country_code VARCHAR(2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    seed BIGINT NOT NULL,
    sales_count INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_pos_seed_run_dates
        CHECK (end_date >= start_date),

    CONSTRAINT uq_pos_seed_run
        UNIQUE (country_code, start_date, end_date, seed)
);

