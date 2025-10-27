-- Business Events Table for Executive KPI Reporting
-- Stores all user interactions, system events, and revenue-generating actions
-- across the ScholarshipAI ecosystem

CREATE TABLE IF NOT EXISTS business_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Request tracing
    request_id UUID NOT NULL,
    
    -- App identification
    app VARCHAR(50) NOT NULL,
    env VARCHAR(20) NOT NULL DEFAULT 'production',
    
    -- Event metadata
    event_name VARCHAR(100) NOT NULL,
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Actor information
    actor_type VARCHAR(20) NOT NULL CHECK (actor_type IN ('student', 'provider', 'system', 'admin')),
    actor_id VARCHAR(100),
    session_id VARCHAR(100),
    org_id VARCHAR(100),
    
    -- Event payload
    properties JSONB NOT NULL DEFAULT '{}',
    
    -- Indexing for common query patterns
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_business_events_event_name ON business_events(event_name);
CREATE INDEX IF NOT EXISTS idx_business_events_app ON business_events(app);
CREATE INDEX IF NOT EXISTS idx_business_events_ts ON business_events(ts DESC);
CREATE INDEX IF NOT EXISTS idx_business_events_actor_id ON business_events(actor_id) WHERE actor_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_business_events_request_id ON business_events(request_id);

-- Composite indexes for KPI aggregation queries
CREATE INDEX IF NOT EXISTS idx_business_events_app_event_ts ON business_events(app, event_name, ts DESC);
CREATE INDEX IF NOT EXISTS idx_business_events_actor_event_ts ON business_events(actor_type, event_name, ts DESC);

-- JSONB indexes for properties queries
CREATE INDEX IF NOT EXISTS idx_business_events_properties ON business_events USING GIN(properties);

-- Partitioning hint: Consider partitioning by ts (monthly) when table exceeds 10M rows

COMMENT ON TABLE business_events IS 'Central event store for all ScholarshipAI business events and KPI tracking';
COMMENT ON COLUMN business_events.request_id IS 'Unique request identifier for distributed tracing';
COMMENT ON COLUMN business_events.app IS 'Source application (scholarship_api, student_pilot, etc)';
COMMENT ON COLUMN business_events.env IS 'Environment (production, staging, development)';
COMMENT ON COLUMN business_events.event_name IS 'Snake_case event name (scholarship_viewed, credit_purchased, etc)';
COMMENT ON COLUMN business_events.actor_type IS 'Who triggered the event (student, provider, system, admin)';
COMMENT ON COLUMN business_events.properties IS 'Event-specific metadata in JSONB format';
