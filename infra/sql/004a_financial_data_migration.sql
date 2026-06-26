-- Migration: Add missing columns to income_statements table
-- Run this if you already have the financial_data schema created

-- Add missing expense detail columns to income_statements
ALTER TABLE income_statements 
ADD COLUMN IF NOT EXISTS change_in_inventory DECIMAL(15, 2),
ADD COLUMN IF NOT EXISTS power_fuel_cost DECIMAL(15, 2),
ADD COLUMN IF NOT EXISTS selling_admin_exp DECIMAL(15, 2);

-- Add unique constraint to period_id (for ON CONFLICT in Python script)
ALTER TABLE income_statements 
DROP CONSTRAINT IF EXISTS income_statements_period_id_key;

ALTER TABLE income_statements 
ADD CONSTRAINT income_statements_period_id_key UNIQUE (period_id);

-- Fix balance_sheets column names
ALTER TABLE balance_sheets 
RENAME COLUMN capital_work_in_progress TO capital_wip;

ALTER TABLE balance_sheets 
RENAME COLUMN cash_and_bank TO cash_and_equivalents;

-- Add unique constraint to balance_sheets period_id
ALTER TABLE balance_sheets 
DROP CONSTRAINT IF EXISTS balance_sheets_period_id_key;

ALTER TABLE balance_sheets 
ADD CONSTRAINT balance_sheets_period_id_key UNIQUE (period_id);

-- Add unique constraint to cash_flows period_id
ALTER TABLE cash_flows 
DROP CONSTRAINT IF EXISTS cash_flows_period_id_key;

ALTER TABLE cash_flows 
ADD CONSTRAINT cash_flows_period_id_key UNIQUE (period_id);

-- Verify the changes
SELECT 'income_statements columns:' AS info;
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'income_statements' 
ORDER BY ordinal_position;

SELECT 'balance_sheets columns:' AS info;
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'balance_sheets' 
ORDER BY ordinal_position;
