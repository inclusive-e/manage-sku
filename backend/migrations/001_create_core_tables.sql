-- Migration Script: Create Core Tables
-- Run this script to initialize the database schema
-- Usage: psql -U postgres -d sku_db -f migrations/001_create_core_tables.sql

-- Drop existing tables if they exist (for clean migration)
DROP TABLE IF EXISTS features CASCADE;
DROP TABLE IF EXISTS sales_data CASCADE;
DROP TABLE IF EXISTS raw_uploads CASCADE;
DROP TABLE IF EXISTS predictions CASCADE;

-- ============================================
-- Table: raw_uploads
-- Stores metadata about uploaded CSV files
-- ============================================
CREATE TABLE raw_uploads (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT,
    row_count INTEGER,
    column_count INTEGER,
    
    -- Schema and validation info (stored as JSON)
    detected_schema JSONB,
    validation_report JSONB,
    column_mapping JSONB,  -- User-confirmed column mappings
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'uploaded',  -- uploaded, processing, processed, error
    error_message TEXT,
    
    -- Timestamps
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for raw_uploads
CREATE INDEX idx_raw_uploads_status ON raw_uploads(status);
CREATE INDEX idx_raw_uploads_uploaded_at ON raw_uploads(uploaded_at);

-- ============================================
-- Table: sales_data
-- Cleaned and processed sales data
-- Complete daily time series per SKU (no gaps)
-- ============================================
CREATE TABLE sales_data (
    id SERIAL PRIMARY KEY,
    upload_id VARCHAR(36) NOT NULL,
    
    -- Core fields
    date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    sku_id VARCHAR(100) NOT NULL,
    sales_quantity FLOAT,
    sales_revenue FLOAT,
    stock_level FLOAT,
    
    -- Additional fields
    category VARCHAR(100),
    unit_price FLOAT,
    
    -- Source tracking: 'user' = from CSV, 'system' = filled gaps
    source_type VARCHAR(20) NOT NULL DEFAULT 'user',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for sales_data
CREATE INDEX idx_sales_data_upload_id ON sales_data(upload_id);
CREATE INDEX idx_sales_data_sku_id ON sales_data(sku_id);
CREATE INDEX idx_sales_data_date ON sales_data(date);
CREATE INDEX idx_sales_data_upload_sku ON sales_data(upload_id, sku_id);
CREATE INDEX idx_sales_data_source_type ON sales_data(source_type);

-- ============================================
-- Table: features
-- Engineered features for ML/heuristic forecasting
-- Generated from sales_data table
-- ============================================
CREATE TABLE features (
    id SERIAL PRIMARY KEY,
    upload_id VARCHAR(36) NOT NULL,
    sku_id VARCHAR(100) NOT NULL,
    date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    
    -- Core target
    sales_quantity FLOAT NOT NULL,
    unit_price FLOAT,
    
    -- Lag features (essential for heuristics)
    lag_7d FLOAT,   -- Last week
    lag_28d FLOAT,  -- Same week last month
    
    -- Rolling averages (trends)
    rolling_mean_7d FLOAT,   -- Short-term trend
    rolling_mean_28d FLOAT,  -- Monthly average
    
    -- Calendar features (seasonality)
    day_of_week INTEGER,     -- 0=Monday, 6=Sunday
    week_of_year INTEGER,    -- 1-53
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for features
CREATE INDEX idx_features_upload_id ON features(upload_id);
CREATE INDEX idx_features_sku_id ON features(sku_id);
CREATE INDEX idx_features_date ON features(date);
CREATE INDEX idx_features_upload_sku ON features(upload_id, sku_id);

-- ============================================
-- Table: predictions
-- Stores forecast/prediction results
-- ============================================
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    input_data JSONB NOT NULL,
    prediction_result JSONB NOT NULL,
    confidence FLOAT,
    model_version VARCHAR(50) DEFAULT 'latest',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for predictions
CREATE INDEX idx_predictions_created_at ON predictions(created_at);

-- ============================================
-- Migration Complete
-- ============================================
SELECT 'Migration 001_create_core_tables completed successfully' as status;
