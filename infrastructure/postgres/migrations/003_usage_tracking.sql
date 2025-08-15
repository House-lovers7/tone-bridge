-- Migration: 003_usage_tracking.sql
-- Purpose: Usage tracking and KPI metrics for ToneBridge
-- Created: 2025-08-12

-- Create transformation_logs table for detailed logging
CREATE TABLE IF NOT EXISTS transformation_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    -- Transformation details
    feature_used VARCHAR(50) NOT NULL, -- tone, structure, summarize, terminology, requirement_structure, background_completion, priority_scoring
    transformation_type VARCHAR(50),
    source_platform VARCHAR(50), -- slack, teams, discord, outlook, web
    -- Text metrics
    input_length INTEGER,
    output_length INTEGER,
    tone_adjustment_level INTEGER, -- 0-3 slider value
    -- Performance metrics
    response_time_ms INTEGER,
    llm_tokens_used INTEGER,
    cache_hit BOOLEAN DEFAULT false,
    -- Results
    success BOOLEAN DEFAULT true,
    error_code VARCHAR(50),
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create usage_summary table for aggregated metrics
CREATE TABLE IF NOT EXISTS usage_summary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    period_type VARCHAR(20) NOT NULL, -- daily, weekly, monthly
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    -- Usage counts
    total_transformations INTEGER DEFAULT 0,
    tone_transformations INTEGER DEFAULT 0,
    structure_transformations INTEGER DEFAULT 0,
    summarizations INTEGER DEFAULT 0,
    requirement_structuring INTEGER DEFAULT 0,
    background_completions INTEGER DEFAULT 0,
    priority_scorings INTEGER DEFAULT 0,
    -- Platform breakdown
    slack_usage INTEGER DEFAULT 0,
    teams_usage INTEGER DEFAULT 0,
    discord_usage INTEGER DEFAULT 0,
    outlook_usage INTEGER DEFAULT 0,
    web_usage INTEGER DEFAULT 0,
    -- Performance metrics
    avg_response_time_ms INTEGER,
    total_tokens_used INTEGER,
    cache_hit_rate DECIMAL(5,2),
    -- User metrics
    active_users INTEGER DEFAULT 0,
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, period_type, period_start)
);

-- Create kpi_metrics table for business metrics
CREATE TABLE IF NOT EXISTS kpi_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    -- Engagement metrics
    daily_active_users INTEGER DEFAULT 0,
    weekly_active_users INTEGER DEFAULT 0,
    monthly_active_users INTEGER DEFAULT 0,
    -- Quality metrics
    misunderstanding_prevention_rate DECIMAL(5,2), -- percentage
    response_time_reduction_rate DECIMAL(5,2), -- percentage
    clarity_improvement_score DECIMAL(5,2), -- 0-100
    -- Business metrics
    feature_adoption_rate JSONB DEFAULT '{}', -- per-feature adoption
    user_satisfaction_score DECIMAL(3,1), -- 1-5 scale
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, metric_date)
);

-- Create custom_dictionaries_tenant table (extending existing custom_dictionaries)
CREATE TABLE IF NOT EXISTS custom_dictionaries_tenant (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    term VARCHAR(255) NOT NULL,
    replacement VARCHAR(255) NOT NULL,
    context VARCHAR(100), -- technical_to_business, business_to_technical, internal_jargon
    category VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, term, context)
);

-- Create custom_tone_settings table
CREATE TABLE IF NOT EXISTS custom_tone_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    -- Tone parameters (0-100 scale)
    formality_level INTEGER DEFAULT 50,
    warmth_level INTEGER DEFAULT 50,
    directness_level INTEGER DEFAULT 50,
    technical_level INTEGER DEFAULT 50,
    -- Custom instructions
    system_prompt TEXT,
    example_transformations JSONB DEFAULT '[]',
    -- Status
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, name)
);

-- Create transformation_feedback table for quality tracking
CREATE TABLE IF NOT EXISTS transformation_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transformation_log_id UUID REFERENCES transformation_logs(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    -- Feedback
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    was_helpful BOOLEAN,
    was_accurate BOOLEAN,
    feedback_text TEXT,
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_transformation_logs_tenant_id ON transformation_logs(tenant_id);
CREATE INDEX idx_transformation_logs_user_id ON transformation_logs(user_id);
CREATE INDEX idx_transformation_logs_created_at ON transformation_logs(created_at DESC);
CREATE INDEX idx_transformation_logs_feature ON transformation_logs(feature_used);
CREATE INDEX idx_transformation_logs_platform ON transformation_logs(source_platform);

CREATE INDEX idx_usage_summary_tenant_id ON usage_summary(tenant_id);
CREATE INDEX idx_usage_summary_period ON usage_summary(period_type, period_start);

CREATE INDEX idx_kpi_metrics_tenant_id ON kpi_metrics(tenant_id);
CREATE INDEX idx_kpi_metrics_date ON kpi_metrics(metric_date DESC);

CREATE INDEX idx_custom_dictionaries_tenant ON custom_dictionaries_tenant(tenant_id);
CREATE INDEX idx_custom_tone_settings_tenant ON custom_tone_settings(tenant_id);

CREATE INDEX idx_transformation_feedback_tenant ON transformation_feedback(tenant_id);
CREATE INDEX idx_transformation_feedback_rating ON transformation_feedback(rating);

-- Add triggers
CREATE TRIGGER update_usage_summary_updated_at BEFORE UPDATE ON usage_summary
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_custom_dictionaries_tenant_updated_at BEFORE UPDATE ON custom_dictionaries_tenant
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_custom_tone_settings_updated_at BEFORE UPDATE ON custom_tone_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE transformation_logs IS 'Detailed log of every transformation request';
COMMENT ON TABLE usage_summary IS 'Aggregated usage statistics per tenant';
COMMENT ON TABLE kpi_metrics IS 'Business KPI metrics for dashboard';
COMMENT ON TABLE custom_dictionaries_tenant IS 'Tenant-specific term replacements';
COMMENT ON TABLE custom_tone_settings IS 'Custom tone profiles per tenant';
COMMENT ON TABLE transformation_feedback IS 'User feedback on transformation quality';