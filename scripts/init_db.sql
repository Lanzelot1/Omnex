-- Initial database setup for Omnex
-- This file is automatically run when PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create initial schema
CREATE SCHEMA IF NOT EXISTS omnex;

-- Set search path
SET search_path TO omnex, public;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Omnex database initialized successfully';
END $$;