-- Migration: Create tables for Net Worth Tracker & Financial Engine

CREATE TABLE IF NOT EXISTS account_balances (
    id SERIAL PRIMARY KEY,
    account_name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL CHECK (account_type IN ('asset', 'liability')),
    balance_inr NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    monthly_return_pct NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS special_asset_holdings (
    id SERIAL PRIMARY KEY,
    asset_key VARCHAR(50) UNIQUE NOT NULL,
    asset_name VARCHAR(100) NOT NULL,
    quantity NUMERIC(15, 4) NOT NULL DEFAULT 0.0000,
    manual_price_override_inr NUMERIC(15, 2) DEFAULT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_account_balances_type ON account_balances (account_type);
CREATE INDEX IF NOT EXISTS idx_special_asset_key ON special_asset_holdings (asset_key);

-- Seed initial default 4 special investment assets if missing
INSERT INTO special_asset_holdings (asset_key, asset_name, quantity)
VALUES 
    ('uber_stock', 'Uber Technologies (UBER)', 15.0),
    ('accenture_stock', 'Accenture plc (ACN)', 5.0),
    ('gold_10g', 'Gold 24K (10-Gram units)', 2.0),
    ('silver_1kg', 'Silver (1-Kg units)', 1.0)
ON CONFLICT (asset_key) DO NOTHING;

-- Seed initial sample accounts if table is empty
INSERT INTO account_balances (account_name, account_type, balance_inr, monthly_return_pct)
SELECT 'HDFC Savings Account', 'asset', 250000.00, 0.30
WHERE NOT EXISTS (SELECT 1 FROM account_balances);

INSERT INTO account_balances (account_name, account_type, balance_inr, monthly_return_pct)
SELECT 'Zerodha Equity & MF', 'asset', 450000.00, 1.00
WHERE NOT EXISTS (SELECT 1 FROM account_balances LIMIT 1 OFFSET 1);

INSERT INTO account_balances (account_name, account_type, balance_inr, monthly_return_pct)
SELECT 'SBI Home Loan', 'liability', 1500000.00, 0.71
WHERE NOT EXISTS (SELECT 1 FROM account_balances LIMIT 1 OFFSET 2);
