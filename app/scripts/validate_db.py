# /root/telecom-customer-service/app/scripts/validate_db.py
import asyncio
import sys
import os

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from app.core.database import db

async def validate_database():
    try:
        print("Testing database connection...")
        await db.connect()
        
        # Check tables
        tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'telecom'
        """
        tables = await db.fetch_all(tables_query)
        print("\nFound tables:")
        for table in tables:
            print(f"- {table['table_name']}")
            
        # Check indices
        indices_query = """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'telecom'
        """
        indices = await db.fetch_all(indices_query)
        print("\nFound indices:")
        for index in indices:
            print(f"- {index['indexname']}")

    except Exception as e:
        print(f"Validation error: {str(e)}")
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(validate_database())