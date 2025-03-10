-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS telecom;

-- Create PDF documents table
CREATE TABLE IF NOT EXISTS telecom.pdf_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create PDF content cache table
CREATE TABLE IF NOT EXISTS telecom.pdf_content_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pdf_id UUID REFERENCES telecom.pdf_documents(id),
    content_hash VARCHAR(64) NOT NULL,
    page_number INTEGER,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(content_hash, page_number)
);

-- Create indices for better performance
CREATE INDEX IF NOT EXISTS idx_pdf_documents_customer_id ON telecom.pdf_documents(customer_id);
CREATE INDEX IF NOT EXISTS idx_pdf_content_cache_hash ON telecom.pdf_content_cache(content_hash);
CREATE INDEX IF NOT EXISTS idx_pdf_documents_filename ON telecom.pdf_documents(filename);

-- Create function for cleaning old cache entries
CREATE OR REPLACE FUNCTION telecom.cleanup_old_cache() RETURNS void AS $$
BEGIN
    DELETE FROM telecom.pdf_content_cache 
    WHERE created_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS telecom.rate_limit_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(20) NOT NULL,
    queue_length INTEGER NOT NULL,
    rate_limited_requests INTEGER NOT NULL,
    token_usage INTEGER NOT NULL,
    avg_response_time FLOAT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES telecom.customers(id)
);

-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_rate_limit_metrics_customer_id 
    ON telecom.rate_limit_metrics(customer_id);
CREATE INDEX IF NOT EXISTS idx_rate_limit_metrics_created_at 
    ON telecom.rate_limit_metrics(created_at);

-- Create cleanup function for old metrics
CREATE OR REPLACE FUNCTION telecom.cleanup_old_metrics() 
RETURNS void AS $$
BEGIN
    DELETE FROM telecom.rate_limit_metrics 
    WHERE created_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;