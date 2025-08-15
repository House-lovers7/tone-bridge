-- Migration: 002_subscriptions.sql
-- Purpose: Subscription and billing management for ToneBridge
-- Created: 2025-08-12

-- Create subscription_plans table (master data)
CREATE TABLE IF NOT EXISTS subscription_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    price_monthly INTEGER NOT NULL, -- in yen
    price_yearly INTEGER, -- in yen
    -- Feature limits
    max_users INTEGER,
    max_platforms INTEGER DEFAULT 1,
    max_transformations_per_month INTEGER,
    max_custom_dictionaries INTEGER DEFAULT 0,
    -- Features flags
    features JSONB DEFAULT '{}',
    -- Status
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default plans
INSERT INTO subscription_plans (name, display_name, price_monthly, price_yearly, max_users, max_platforms, max_transformations_per_month, max_custom_dictionaries, features) VALUES
('standard', 'スタンダード', 500, 5000, 5, 1, 1000, 0, '{"tone_transform": true, "summarize": true}'),
('pro', 'プロ', 1000, 10000, 20, 3, 5000, 5, '{"tone_transform": true, "summarize": true, "structure": true, "background_completion": true, "priority_scoring": true}'),
('enterprise', 'エンタープライズ', 150000, 1500000, NULL, NULL, NULL, NULL, '{"all_features": true, "custom_domain": true, "sso": true, "api_access": true, "sla": true}')
ON CONFLICT (name) DO NOTHING;

-- Create subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES subscription_plans(id),
    -- Billing
    billing_cycle VARCHAR(20) NOT NULL DEFAULT 'monthly', -- monthly, yearly
    price_per_cycle INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'JPY',
    -- Status
    status VARCHAR(50) DEFAULT 'active', -- active, canceled, past_due, trialing
    trial_ends_at TIMESTAMP WITH TIME ZONE,
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    canceled_at TIMESTAMP WITH TIME ZONE,
    -- Payment
    payment_method VARCHAR(50), -- card, invoice, bank_transfer
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id)
);

-- Create billing_history table
CREATE TABLE IF NOT EXISTS billing_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES subscriptions(id),
    -- Invoice details
    invoice_number VARCHAR(100) UNIQUE,
    amount INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'JPY',
    description TEXT,
    -- Period
    billing_period_start DATE,
    billing_period_end DATE,
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, paid, failed, refunded
    paid_at TIMESTAMP WITH TIME ZONE,
    -- Payment
    payment_method VARCHAR(50),
    stripe_invoice_id VARCHAR(255),
    stripe_payment_intent_id VARCHAR(255),
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create feature_usage_limits table for custom limits
CREATE TABLE IF NOT EXISTS feature_usage_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    limit_value INTEGER,
    reset_period VARCHAR(20) DEFAULT 'monthly', -- daily, weekly, monthly
    custom_settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, feature_name)
);

-- Create indexes
CREATE INDEX idx_subscriptions_tenant_id ON subscriptions(tenant_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_current_period_end ON subscriptions(current_period_end);
CREATE INDEX idx_billing_history_tenant_id ON billing_history(tenant_id);
CREATE INDEX idx_billing_history_status ON billing_history(status);
CREATE INDEX idx_billing_history_created_at ON billing_history(created_at DESC);
CREATE INDEX idx_feature_usage_limits_tenant_id ON feature_usage_limits(tenant_id);

-- Add triggers
CREATE TRIGGER update_subscription_plans_updated_at BEFORE UPDATE ON subscription_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_feature_usage_limits_updated_at BEFORE UPDATE ON feature_usage_limits
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE subscriptions IS 'Active subscriptions for each tenant';
COMMENT ON TABLE billing_history IS 'Historical billing records and invoices';
COMMENT ON TABLE feature_usage_limits IS 'Custom feature limits per tenant';