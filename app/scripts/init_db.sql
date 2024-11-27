-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schema
CREATE SCHEMA IF NOT EXISTS telecom;

-- Create PDF documents table
CREATE TABLE IF NOT EXISTS telecom.pdf_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(20) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    path VARCHAR(255) NOT NULL,
    date TIMESTAMPTZ,
    pages INTEGER,
    size BIGINT,
    preview TEXT,
    content_hash VARCHAR(64) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_valid BOOLEAN DEFAULT true,
    metadata JSONB
);

-- Create PDF content cache table
CREATE TABLE IF NOT EXISTS telecom.pdf_content_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pdf_id UUID REFERENCES telecom.pdf_documents(id),
    content_hash VARCHAR(64) NOT NULL,
    page_number INTEGER,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(content_hash, page_number)
);

-- Create indices
CREATE INDEX IF NOT EXISTS idx_pdf_documents_customer_id ON telecom.pdf_documents(customer_id);
CREATE INDEX IF NOT EXISTS idx_pdf_content_cache_hash ON telecom.pdf_content_cache(content_hash);
CREATE INDEX IF NOT EXISTS idx_pdf_documents_filename ON telecom.pdf_documents(filename);