import asyncio
import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.session.manager import SessionManager

async def test_session():
    manager = SessionManager()
    
    try:
        # Test health
        health = await manager.check_health()
        print(f"Redis health: {health}")

        # Create session
        session = await manager.create_session("3694388")
        print(f"Created session: {session}")

        # Retrieve session
        if session:
            retrieved = await manager.get_session(session['id'])
            print(f"Retrieved session: {retrieved}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_session())
