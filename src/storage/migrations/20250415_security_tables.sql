-- Migration: Security Tables
-- Description: Creates tables for token revocation and security monitoring

-- Create revoked_tokens table
CREATE TABLE IF NOT EXISTS revoked_tokens (
    id SERIAL PRIMARY KEY,
    jti VARCHAR(255) NOT NULL,
    user_id UUID,
    revoked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(jti)
);

-- Create index on jti for faster lookups
CREATE INDEX IF NOT EXISTS idx_revoked_tokens_jti ON revoked_tokens(jti);

-- Create index on user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_revoked_tokens_user_id ON revoked_tokens(user_id);

-- Create revoked_users table
CREATE TABLE IF NOT EXISTS revoked_users (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Create index on user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_revoked_users_user_id ON revoked_users(user_id);

-- Create security_events table
CREATE TABLE IF NOT EXISTS security_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    user_id UUID,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    severity VARCHAR(50) NOT NULL DEFAULT 'info',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create index on event_type for faster lookups
CREATE INDEX IF NOT EXISTS idx_security_events_event_type ON security_events(event_type);

-- Create index on user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security_events(user_id);

-- Create index on severity for faster lookups
CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security_events(severity);

-- Create security_alerts table
CREATE TABLE IF NOT EXISTS security_alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(255) NOT NULL,
    user_id UUID,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    severity VARCHAR(50) NOT NULL DEFAULT 'info',
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create index on alert_type for faster lookups
CREATE INDEX IF NOT EXISTS idx_security_alerts_alert_type ON security_alerts(alert_type);

-- Create index on user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_security_alerts_user_id ON security_alerts(user_id);

-- Create index on severity for faster lookups
CREATE INDEX IF NOT EXISTS idx_security_alerts_severity ON security_alerts(severity);

-- Create index on is_resolved for faster lookups
CREATE INDEX IF NOT EXISTS idx_security_alerts_is_resolved ON security_alerts(is_resolved);

-- Create resource_metrics table
CREATE TABLE IF NOT EXISTS resource_metrics (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    room_count INTEGER NOT NULL DEFAULT 0,
    participant_count INTEGER NOT NULL DEFAULT 0,
    subscription_count INTEGER NOT NULL DEFAULT 0,
    token_count INTEGER NOT NULL DEFAULT 0,
    bandwidth_usage FLOAT NOT NULL DEFAULT 0.0,
    cpu_usage FLOAT NOT NULL DEFAULT 0.0,
    memory_usage FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create index on user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_resource_metrics_user_id ON resource_metrics(user_id);

-- Create index on created_at for faster lookups
CREATE INDEX IF NOT EXISTS idx_resource_metrics_created_at ON resource_metrics(created_at);

-- Create RLS policies for revoked_tokens
ALTER TABLE revoked_tokens ENABLE ROW LEVEL SECURITY;

CREATE POLICY revoked_tokens_select ON revoked_tokens
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY revoked_tokens_insert ON revoked_tokens
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

-- Create RLS policies for revoked_users
ALTER TABLE revoked_users ENABLE ROW LEVEL SECURITY;

CREATE POLICY revoked_users_select ON revoked_users
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY revoked_users_insert ON revoked_users
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

-- Create RLS policies for security_events
ALTER TABLE security_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY security_events_select ON security_events
    FOR SELECT
    USING (auth.role() = 'authenticated' AND (user_id = auth.uid() OR auth.role() = 'service_role'));

CREATE POLICY security_events_insert ON security_events
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

-- Create RLS policies for security_alerts
ALTER TABLE security_alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY security_alerts_select ON security_alerts
    FOR SELECT
    USING (auth.role() = 'authenticated' AND (user_id = auth.uid() OR auth.role() = 'service_role'));

CREATE POLICY security_alerts_insert ON security_alerts
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY security_alerts_update ON security_alerts
    FOR UPDATE
    USING (auth.role() = 'authenticated' AND (user_id = auth.uid() OR auth.role() = 'service_role'));

-- Create RLS policies for resource_metrics
ALTER TABLE resource_metrics ENABLE ROW LEVEL SECURITY;

CREATE POLICY resource_metrics_select ON resource_metrics
    FOR SELECT
    USING (auth.role() = 'authenticated' AND (user_id = auth.uid() OR auth.role() = 'service_role'));

CREATE POLICY resource_metrics_insert ON resource_metrics
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

-- Add function to clean up expired tokens
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS void AS $$
BEGIN
    DELETE FROM revoked_tokens
    WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to clean up expired tokens daily
-- Note: This requires pg_cron extension to be enabled
-- UNCOMMENT THIS SECTION IF pg_cron IS AVAILABLE
-- SELECT cron.schedule('0 0 * * *', 'SELECT cleanup_expired_tokens()');