-- Create chat history table if not exists
CREATE TABLE IF NOT EXISTS telecom.chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES telecom.sessions(id),
    message_type VARCHAR(10) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    pdf_context UUID REFERENCES telecom.pdf_documents(id),
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT valid_message_type CHECK (message_type IN ('user', 'bot', 'system'))
);

-- Create indices for better performance
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created 
ON telecom.chat_messages(session_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at 
ON telecom.chat_messages(created_at DESC);

-- Create cleanup function
CREATE OR REPLACE FUNCTION telecom.cleanup_old_chat_messages()
RETURNS void AS $$
BEGIN
    DELETE FROM telecom.chat_messages
    WHERE created_at < NOW() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;