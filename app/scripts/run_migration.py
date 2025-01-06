# app/scripts/run_migration.py

import asyncio
from app.core.database import db

async def run_migration():
    try:
        # SQL for creating the rate limit metrics table
        migration_sql = """
        CREATE TABLE IF NOT EXISTS telecom.rate_limit_metrics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            customer_id VARCHAR(20) NOT NULL,
            queue_length INTEGER NOT NULL DEFAULT 0,
            rate_limited_requests INTEGER NOT NULL DEFAULT 0,
            token_usage INTEGER NOT NULL DEFAULT 0,
            avg_response_time FLOAT NOT NULL DEFAULT 0.0,
            is_cached BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_customer
                FOREIGN KEY (customer_id) 
                REFERENCES telecom.customers(id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_rate_limit_metrics_customer 
            ON telecom.rate_limit_metrics(customer_id);
        CREATE INDEX IF NOT EXISTS idx_rate_limit_metrics_timestamp 
            ON telecom.rate_limit_metrics(created_at);

        CREATE OR REPLACE FUNCTION telecom.cleanup_old_rate_limit_metrics()
        RETURNS void AS $$
        BEGIN
            DELETE FROM telecom.rate_limit_metrics 
            WHERE created_at < NOW() - INTERVAL '7 days';
        END;
        $$ LANGUAGE plpgsql;
        """

        # Connect to database
        await db.connect()
        
        # Execute migration
        await db.execute(migration_sql)
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error running migration: {str(e)}")
    finally:
        # Close database connection
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(run_migration())