from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.chat_history.service import chat_history_service
import logging

logger = logging.getLogger(__name__)

def setup_cleanup_jobs(scheduler: AsyncIOScheduler):
    """Setup cleanup jobs"""
    try:
        scheduler.add_job(
            chat_history_service.cleanup_old_history,
            'cron', 
            hour=3,  # Run at 3 AM
            kwargs={'days': 90},
            id='cleanup_chat_history',
            replace_existing=True
        )
        logger.info("Chat history cleanup job scheduled")
    except Exception as e:
        logger.error(f"Error setting up cleanup job: {e}")
        raise