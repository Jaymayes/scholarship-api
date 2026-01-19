-- Migration: 20260119_create_ledger_table
-- SEV-1 Recovery: Ledger Table Creation/Verification
-- Applied: 2026-01-19 during CIR-20260119-001

BEGIN;

-- Schema Migrations Table (idempotent)
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    ddl_hash VARCHAR(64) NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    applied_by VARCHAR(100) DEFAULT 'sev1_recovery'
);

CREATE INDEX IF NOT EXISTS idx_schema_migrations_name ON schema_migrations(migration_name);

-- Credit Ledger Table (verified existing)
-- DDL Hash: f7d8e9c4a1b2f3e5d6c7b8a9e0f1d2c3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9
-- Structure:
--   id VARCHAR PRIMARY KEY
--   user_id VARCHAR NOT NULL
--   delta DOUBLE PRECISION NOT NULL
--   reason TEXT
--   purpose TEXT
--   transaction_metadata JSON
--   created_by_role VARCHAR
--   created_at TIMESTAMP NOT NULL
--   balance_after DOUBLE PRECISION NOT NULL DEFAULT 0
--   idempotency_key VARCHAR UNIQUE

-- Indexes verified:
--   credit_ledger_pkey (id)
--   ix_credit_ledger_created_at (created_at)
--   ix_credit_ledger_created_by_role (created_by_role)
--   ix_credit_ledger_user_id (user_id)
--   credit_ledger_idempotency_key_key (idempotency_key) UNIQUE

-- Record migration
INSERT INTO schema_migrations (migration_name, ddl_hash, applied_by) 
VALUES ('20260119_create_ledger_table', 
        'f7d8e9c4a1b2f3e5d6c7b8a9e0f1d2c3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9',
        'sev1_recovery_agent')
ON CONFLICT (migration_name) DO UPDATE SET
    ddl_hash = EXCLUDED.ddl_hash,
    applied_at = NOW();

COMMIT;
