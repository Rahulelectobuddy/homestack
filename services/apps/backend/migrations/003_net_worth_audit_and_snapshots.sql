-- Migration: Create account_audit_logs and net_worth_snapshots tables

CREATE TABLE IF NOT EXISTS account_audit_logs (
    id SERIAL PRIMARY KEY,
    account_id INT NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    action_type VARCHAR(50) NOT NULL CHECK (action_type IN ('CREATE', 'UPDATE', 'DELETE')),
    old_balance_inr NUMERIC(15, 2) DEFAULT NULL,
    new_balance_inr NUMERIC(15, 2) DEFAULT NULL,
    old_monthly_return_pct NUMERIC(5, 2) DEFAULT NULL,
    new_monthly_return_pct NUMERIC(5, 2) DEFAULT NULL,
    change_reason VARCHAR(500) DEFAULT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS net_worth_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_date DATE NOT NULL UNIQUE,
    net_worth_inr NUMERIC(15, 2) NOT NULL,
    total_assets_inr NUMERIC(15, 2) NOT NULL,
    total_liabilities_inr NUMERIC(15, 2) NOT NULL,
    account_assets_inr NUMERIC(15, 2) NOT NULL,
    special_investments_inr NUMERIC(15, 2) NOT NULL,
    projected_monthly_income_inr NUMERIC(15, 2) NOT NULL,
    details_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_account_id ON account_audit_logs (account_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_date ON net_worth_snapshots (snapshot_date);
