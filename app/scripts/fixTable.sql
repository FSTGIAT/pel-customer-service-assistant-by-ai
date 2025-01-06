CREATE TABLE telecom.pdf_content_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pdf_id UUID REFERENCES telecom.pdf_documents(id),
    content_hash VARCHAR(64) NOT NULL,
    page_number INTEGER,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(content_hash, page_number)
);

CREATE INDEX idx_pdf_content_cache_hash ON telecom.pdf_content_cache(content_hash);
