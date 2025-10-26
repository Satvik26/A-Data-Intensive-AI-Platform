-- Atlas Platform - Database Initialization Script
-- This script runs on first PostgreSQL container startup

-- Create test database
CREATE DATABASE atlas_test;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE atlas_dev TO atlas;
GRANT ALL PRIVILEGES ON DATABASE atlas_test TO atlas;

-- Enable required extensions on atlas_dev
\c atlas_dev;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Enable required extensions on atlas_test
\c atlas_test;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

