-- Migration: 001_tenants.sql
-- Purpose: Multi-tenant support for ToneBridge
-- Created: 2025-08-12

-- Create tenants table
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan_type VARCHAR(50) DEFAULT 'standard',
    custom_settings JSONB DEFAULT '{}',
    -- Contact information
    primary_contact_email VARCHAR(255),
    billing_email VARCHAR(255),
    -- Status
    status VARCHAR(50) DEFAULT 'active',
    trial_ends_at TIMESTAMP WITH TIME ZONE,
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add tenant_id to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;

-- Create tenant_members table for user-tenant relationships
CREATE TABLE IF NOT EXISTS tenant_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member', -- owner, admin, member
    permissions JSONB DEFAULT '{}',
    invited_by UUID REFERENCES users(id),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, user_id)
);

-- Create tenant_invitations table
CREATE TABLE IF NOT EXISTS tenant_invitations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'member',
    token VARCHAR(255) UNIQUE NOT NULL,
    invited_by UUID REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'pending',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes
CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_status ON tenants(status);
CREATE INDEX idx_tenant_members_tenant_id ON tenant_members(tenant_id);
CREATE INDEX idx_tenant_members_user_id ON tenant_members(user_id);
CREATE INDEX idx_tenant_invitations_token ON tenant_invitations(token);
CREATE INDEX idx_tenant_invitations_email ON tenant_invitations(email);

-- Add trigger for updated_at
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE tenants IS 'Multi-tenant organizations using ToneBridge';
COMMENT ON COLUMN tenants.plan_type IS 'standard, pro, or enterprise';
COMMENT ON COLUMN tenants.custom_settings IS 'JSON settings for custom tone, dictionaries, etc.';