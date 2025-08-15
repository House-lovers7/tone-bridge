-- Auto-transformation mode settings and rules

-- Auto-transform configurations per tenant
CREATE TABLE IF NOT EXISTS auto_transform_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Global settings
    default_transformation_type VARCHAR(50) DEFAULT 'soften',
    default_intensity INTEGER DEFAULT 2 CHECK (default_intensity >= 0 AND default_intensity <= 3),
    
    -- Detection settings
    min_message_length INTEGER DEFAULT 50, -- Minimum characters to trigger
    max_processing_delay_ms INTEGER DEFAULT 500, -- Max delay before processing
    
    -- Behavior settings
    require_confirmation BOOLEAN DEFAULT true,
    show_preview BOOLEAN DEFAULT true,
    preserve_original BOOLEAN DEFAULT true,
    
    UNIQUE(tenant_id)
);

-- Auto-transform rules (conditions that trigger transformation)
CREATE TABLE IF NOT EXISTS auto_transform_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID NOT NULL REFERENCES auto_transform_configs(id) ON DELETE CASCADE,
    rule_name VARCHAR(255) NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0, -- Higher priority rules are evaluated first
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Trigger conditions
    trigger_type VARCHAR(50) NOT NULL, -- 'keyword', 'sentiment', 'recipient', 'channel', 'time', 'pattern'
    trigger_value JSONB NOT NULL, -- Flexible JSON for various trigger configurations
    
    -- Transformation settings
    transformation_type VARCHAR(50) NOT NULL,
    transformation_intensity INTEGER DEFAULT 2,
    transformation_options JSONB DEFAULT '{}',
    
    -- Scope
    platforms TEXT[] DEFAULT '{}', -- Empty means all platforms
    channels TEXT[] DEFAULT '{}', -- Specific channels/groups
    user_roles TEXT[] DEFAULT '{}', -- Apply to specific user roles
    
    INDEX idx_auto_rules_config (config_id),
    INDEX idx_auto_rules_priority (priority DESC)
);

-- Predefined rule templates
CREATE TABLE IF NOT EXISTS auto_transform_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL,
    description TEXT,
    rule_config JSONB NOT NULL,
    is_system BOOLEAN DEFAULT false, -- System templates cannot be deleted
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Auto-transform activity log
CREATE TABLE IF NOT EXISTS auto_transform_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    rule_id UUID REFERENCES auto_transform_rules(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Message details
    original_message TEXT NOT NULL,
    transformed_message TEXT,
    platform VARCHAR(50) NOT NULL,
    channel_id VARCHAR(255),
    message_id VARCHAR(255),
    
    -- Processing details
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    processing_time_ms INTEGER,
    
    -- Outcome
    status VARCHAR(50) NOT NULL, -- 'triggered', 'transformed', 'skipped', 'failed', 'cancelled'
    skip_reason VARCHAR(255),
    error_message TEXT,
    
    -- User action
    user_action VARCHAR(50), -- 'accepted', 'rejected', 'modified', 'ignored'
    user_feedback TEXT,
    
    INDEX idx_auto_logs_tenant_date (tenant_id, triggered_at DESC),
    INDEX idx_auto_logs_user (user_id),
    INDEX idx_auto_logs_status (status)
);

-- User preferences for auto-transformation
CREATE TABLE IF NOT EXISTS user_auto_transform_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Personal overrides
    enabled BOOLEAN DEFAULT true,
    notification_preference VARCHAR(50) DEFAULT 'inline', -- 'inline', 'popup', 'silent'
    auto_accept_threshold FLOAT DEFAULT 0.9, -- Confidence threshold for auto-accept
    
    -- Platform-specific settings
    platform_settings JSONB DEFAULT '{}',
    
    -- Exclusions
    excluded_channels TEXT[] DEFAULT '{}',
    excluded_recipients TEXT[] DEFAULT '{}',
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, tenant_id)
);

-- Insert default templates
INSERT INTO auto_transform_templates (template_name, category, description, rule_config, is_system) VALUES
-- Executive communication
('Executive Email', 'communication', 'Automatically soften emails to executives', 
 '{"trigger_type": "recipient", "trigger_value": {"roles": ["executive", "c-level"]}, 
   "transformation_type": "soften", "transformation_intensity": 3}', true),

-- Customer support
('Customer Response', 'support', 'Transform support messages for better customer experience',
 '{"trigger_type": "channel", "trigger_value": {"type": "support"}, 
   "transformation_type": "soften", "transformation_intensity": 2,
   "transformation_options": {"add_empathy": true, "include_apology": true}}', true),

-- Technical documentation
('Tech to Non-Tech', 'documentation', 'Convert technical language for non-technical audience',
 '{"trigger_type": "keyword", "trigger_value": {"keywords": ["API", "database", "backend", "frontend", "deployment"]},
   "transformation_type": "terminology", "transformation_intensity": 2}', true),

-- Urgent messages
('Urgent Clarification', 'priority', 'Auto-structure urgent messages',
 '{"trigger_type": "keyword", "trigger_value": {"keywords": ["urgent", "ASAP", "critical", "emergency"]},
   "transformation_type": "structure", "transformation_intensity": 3}', true),

-- Negative sentiment
('Tone Adjustment', 'sentiment', 'Soften messages with negative sentiment',
 '{"trigger_type": "sentiment", "trigger_value": {"threshold": -0.5, "operator": "less_than"},
   "transformation_type": "soften", "transformation_intensity": 2}', true),

-- Time-based
('End of Day Summary', 'schedule', 'Structure end-of-day updates',
 '{"trigger_type": "time", "trigger_value": {"after": "17:00", "before": "19:00"},
   "transformation_type": "summarize", "transformation_intensity": 2}', true),

-- Meeting notes
('Meeting Notes Structure', 'meetings', 'Auto-structure meeting notes',
 '{"trigger_type": "pattern", "trigger_value": {"patterns": ["meeting notes", "action items", "follow-up"]},
   "transformation_type": "requirement_structuring", "transformation_intensity": 2}', true);

-- Create indexes for performance
CREATE INDEX idx_auto_config_tenant ON auto_transform_configs(tenant_id);
CREATE INDEX idx_auto_rules_enabled ON auto_transform_rules(enabled) WHERE enabled = true;
CREATE INDEX idx_auto_logs_recent ON auto_transform_logs(triggered_at DESC);

-- Add column to track auto-transformations in main transformation logs
ALTER TABLE transformation_logs 
ADD COLUMN IF NOT EXISTS is_auto_transform BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS auto_rule_id UUID REFERENCES auto_transform_rules(id) ON DELETE SET NULL;