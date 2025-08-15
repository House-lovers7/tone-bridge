-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    organization VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create transformations table
CREATE TABLE IF NOT EXISTS transformations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    original_text TEXT NOT NULL,
    transformed_text TEXT NOT NULL,
    transformation_type VARCHAR(50) NOT NULL,
    source_tone VARCHAR(50),
    target_tone VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create custom_dictionaries table
CREATE TABLE IF NOT EXISTS custom_dictionaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization VARCHAR(255),
    term VARCHAR(255) NOT NULL,
    definition TEXT,
    category VARCHAR(100),
    alternatives JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create term_embeddings table for semantic search
CREATE TABLE IF NOT EXISTS term_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    term VARCHAR(255) NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    source VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(term, source)
);

-- Create analytics_events table
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_transformations_user_id ON transformations(user_id);
CREATE INDEX idx_transformations_created_at ON transformations(created_at DESC);
CREATE INDEX idx_custom_dictionaries_org ON custom_dictionaries(organization);
CREATE INDEX idx_custom_dictionaries_term ON custom_dictionaries(term);
CREATE INDEX idx_term_embeddings_embedding ON term_embeddings USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_analytics_events_user_id ON analytics_events(user_id);
CREATE INDEX idx_analytics_events_timestamp ON analytics_events(timestamp DESC);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_custom_dictionaries_updated_at BEFORE UPDATE ON custom_dictionaries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();