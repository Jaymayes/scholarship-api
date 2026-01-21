# DataService V2 Sprint-2 Migration Strategy

## Overview

This document outlines the migration strategy for the DataService V2 Sprint-2 tables. All models are **additive** - they create new tables without modifying existing schema.

## New Tables

| Table Name | Description | Dependencies |
|------------|-------------|--------------|
| `ds_users` | DataService users with FERPA flags | None |
| `ds_providers` | B2B provider accounts | None |
| `ds_uploads` | File upload metadata | `ds_users` (FK) |
| `ds_ledgers` | Double-entry ledger headers | None |
| `ds_ledger_entries` | Ledger line items | `ds_ledgers` (FK) |
| `ds_events` | Audit trail events | `ds_users` (FK, optional) |

## Migration Steps

### Phase 1: Schema Creation (Non-Destructive)

```sql
-- Run in a transaction
BEGIN;

-- 1. Create ds_users table
CREATE TABLE IF NOT EXISTS ds_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending_verification',
    role VARCHAR(50) NOT NULL DEFAULT 'consumer',
    is_ferpa_covered BOOLEAN NOT NULL DEFAULT FALSE,
    ferpa_consent_date TIMESTAMP,
    profile_data JSONB,
    preferences JSONB,
    last_login_at TIMESTAMP,
    login_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP,
    deleted_by VARCHAR(255)
);

-- 2. Create ds_providers table
CREATE TABLE IF NOT EXISTS ds_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    segment VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'invited',
    contact_email VARCHAR(255) NOT NULL,
    institutional_domain VARCHAR(255) NOT NULL,
    api_key_hash VARCHAR(255) UNIQUE,
    api_key_prefix VARCHAR(20),
    api_key_created_at TIMESTAMP,
    api_key_last_used_at TIMESTAMP,
    is_ferpa_covered BOOLEAN NOT NULL DEFAULT TRUE,
    dpa_signed BOOLEAN NOT NULL DEFAULT FALSE,
    dpa_signed_date TIMESTAMP,
    contract_start_date TIMESTAMP,
    contract_end_date TIMESTAMP,
    monthly_fee FLOAT NOT NULL DEFAULT 0.0,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP,
    deleted_by VARCHAR(255)
);

-- 3. Create ds_uploads table
CREATE TABLE IF NOT EXISTS ds_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES ds_users(id),
    filename VARCHAR(500) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
    is_ferpa_covered BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    storage_path VARCHAR(1000),
    checksum_sha256 VARCHAR(64),
    processed_at TIMESTAMP,
    processing_error TEXT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP,
    deleted_by VARCHAR(255)
);

-- 4. Create ds_ledgers table
CREATE TABLE IF NOT EXISTS ds_ledgers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id UUID UNIQUE NOT NULL,
    description TEXT,
    reference_type VARCHAR(100),
    reference_id UUID,
    validated_at TIMESTAMP,
    is_balanced BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP,
    deleted_by VARCHAR(255)
);

-- 5. Create ds_ledger_entries table
CREATE TABLE IF NOT EXISTS ds_ledger_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ledger_id UUID NOT NULL REFERENCES ds_ledgers(id) ON DELETE CASCADE,
    account_type VARCHAR(50) NOT NULL,
    account_code VARCHAR(50) NOT NULL,
    account_name VARCHAR(255),
    amount FLOAT NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 6. Create ds_events table
CREATE TABLE IF NOT EXISTS ds_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES ds_users(id),
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,
    changes JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    session_id VARCHAR(100),
    is_ferpa_access BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMIT;
```

### Phase 2: Index Creation

```sql
-- Users indexes
CREATE INDEX IF NOT EXISTS ix_ds_users_email_status ON ds_users(email, status);
CREATE INDEX IF NOT EXISTS ix_ds_users_role ON ds_users(role);

-- Providers indexes
CREATE INDEX IF NOT EXISTS ix_ds_providers_segment_status ON ds_providers(segment, status);
CREATE INDEX IF NOT EXISTS ix_ds_providers_api_key_prefix ON ds_providers(api_key_prefix);

-- Uploads indexes
CREATE INDEX IF NOT EXISTS ix_ds_uploads_owner_status ON ds_uploads(owner_id, status);
CREATE INDEX IF NOT EXISTS ix_ds_uploads_ferpa ON ds_uploads(is_ferpa_covered);

-- Ledgers indexes
CREATE INDEX IF NOT EXISTS ix_ds_ledgers_trace_id ON ds_ledgers(trace_id);
CREATE INDEX IF NOT EXISTS ix_ds_ledgers_validated ON ds_ledgers(validated_at);
CREATE INDEX IF NOT EXISTS ix_ds_ledgers_reference ON ds_ledgers(reference_type, reference_id);

-- Ledger entries indexes
CREATE INDEX IF NOT EXISTS ix_ds_ledger_entries_ledger_id ON ds_ledger_entries(ledger_id);
CREATE INDEX IF NOT EXISTS ix_ds_ledger_entries_account ON ds_ledger_entries(account_type, account_code);

-- Events indexes
CREATE INDEX IF NOT EXISTS ix_ds_events_entity ON ds_events(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS ix_ds_events_created ON ds_events(created_at);
CREATE INDEX IF NOT EXISTS ix_ds_events_ferpa ON ds_events(is_ferpa_access, created_at);
CREATE INDEX IF NOT EXISTS ix_ds_events_event_type ON ds_events(event_type);
```

## Rollback Strategy

All migrations are reversible. To rollback:

```sql
-- DANGER: Only run if rollback is required
-- This will delete all data in these tables

DROP TABLE IF EXISTS ds_events CASCADE;
DROP TABLE IF EXISTS ds_ledger_entries CASCADE;
DROP TABLE IF EXISTS ds_ledgers CASCADE;
DROP TABLE IF EXISTS ds_uploads CASCADE;
DROP TABLE IF EXISTS ds_providers CASCADE;
DROP TABLE IF EXISTS ds_users CASCADE;
```

## Using SQLAlchemy Auto-Migration

For development, tables can be created automatically:

```python
from server.v2.dataservice import create_tables

# Creates all DataService tables
create_tables()
```

## Production Deployment Checklist

1. [ ] Backup existing database
2. [ ] Run Phase 1 migration in a transaction
3. [ ] Verify table creation with `\dt ds_*`
4. [ ] Run Phase 2 index creation
5. [ ] Verify indexes with `\di ds_*`
6. [ ] Test `/readyz` endpoint returns healthy
7. [ ] Monitor for migration-related errors in logs

## Data Retention

| Table | Retention Policy |
|-------|------------------|
| `ds_users` | Indefinite (soft delete) |
| `ds_providers` | Indefinite (soft delete) |
| `ds_uploads` | 90 days after deletion |
| `ds_ledgers` | 7 years (compliance) |
| `ds_ledger_entries` | 7 years (compliance) |
| `ds_events` | 2 years (audit trail) |
