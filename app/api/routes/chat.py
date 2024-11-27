from fastapi import APIRouter, HTTPException, Request
from typing import Optional, List
from pydantic import BaseModel
from app.services.claude_service import claude_service
from app.services.pdf_service import pdf_service
from app.services.telecom_bill_processor import bill_processor, query_processor
import logging
from dataclasses import asdict
from app.services.chat_history.service import chat_history_service
from app.services.chat_history.models import ChatMessage
from uuid import UUID
from app.core.database import db
from datetime import datetime
import json
import hashlib
from app.core.redis import redis_client
import aioredis


router = APIRouter()
logger = logging.getLogger(__name__)



class Message(BaseModel):
    type: str
    content: str
    
    

class ChatRequest(BaseModel):
    message: str
    customerId: str
    context: Optional[List[Message]] = []
    pdf_path: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    status: str = "success"
    error: Optional[str] = None
    bill_data: Optional[dict] = None

@router.get("/chat/history/{customer_id}")
async def get_chat_history(customer_id: str, days: int = 30):
    """Get chat history for a customer"""
    try:
        messages = await chat_history_service.get_customer_history(customer_id, days)
        return {
            "status": "success",
            "messages": messages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_pdf_id(path: str, db) -> Optional[UUID]:
    """Get PDF ID from path"""
    try:
        query = """
            SELECT id FROM telecom.pdf_documents 
            WHERE file_path = $1 
            LIMIT 1
        """
        result = await db.fetch_one(query, path)
        return result['id'] if result else None
    except Exception as e:
        logger.error(f"Error getting PDF ID: {e}")
        return None

async def get_pdf_id_from_path(file_path: str) -> Optional[UUID]:
    """Get or create PDF document ID from file path"""
    try:
        query = """
            SELECT id 
            FROM telecom.pdf_documents 
            WHERE path = $1 
            LIMIT 1
        """
        result = await db.fetch_one(query, file_path)
        if result:
            return result['id']
        return None
    except Exception as e:
        logger.error(f"Error getting PDF ID: {e}")
        return None


@router.post("/chat")
async def chat(request: ChatRequest, req: Request):
    try:
        # session handling
        logger.info(f"Request state: {vars(req.state)}")
        session = getattr(req.state, 'session', None)
        logger.info(f"Session found: {session}")

        if not session:
            from uuid import uuid5, NAMESPACE_DNS
            session_key = f"{request.customerId}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            session_id = uuid5(NAMESPACE_DNS, session_key)
            session = {
                'id': session_id,
                'customer_id': request.customerId,
                'created_at': datetime.utcnow().isoformat()
            }
            logger.info(f"Created temporary session: {session}")

        # Add rate limit check
        rate_limit_key = f"rate_limit:{request.customerId}"
        current_requests = await redis_client.get(rate_limit_key)
        if current_requests and int(current_requests) >= 5:  # 5 requests per minute
            raise HTTPException(
                status_code=429, 
                detail="Rate limit exceeded. Please wait before sending more requests."
            )
        await redis_client.incr(rate_limit_key)
        await redis_client.expire(rate_limit_key, 60)  # 1 minute window

        pdfs = await pdf_service.get_customer_pdfs(request.customerId)
        if not pdfs:
            raise HTTPException(status_code=404, detail="No bills found")

        # Your existing PDF ID handling
        current_pdf_id = None
        if request.pdf_path:
            try:
                current_pdf_id = await get_pdf_id_from_path(request.pdf_path)
                logger.info(f"Found PDF ID for path {request.pdf_path}: {current_pdf_id}")
            except Exception as e:
                logger.warning(f"Could not get PDF ID for path {request.pdf_path}: {e}")
        
        if current_pdf_id is None and pdfs:
            try:
                current_pdf_id = await get_pdf_id_from_path(pdfs[0].path)
                logger.info(f"Using first PDF's ID: {current_pdf_id}")
            except Exception as e:
                logger.warning(f"Could not get PDF ID for first PDF: {e}")

        combined_text = []
        for pdf in pdfs:
            pdf_text = await pdf_service.extract_pdf_text(pdf.path)
            if pdf_text:
                bill_section = f"=== חשבונית {pdf.date.strftime('%d/%m/%Y')} ===\n{pdf_text}"
                combined_text.append(bill_section)


        table_instructions = """
בהצגת השוואה בין חשבוניות, אנא השתמש בפורמט הבא:

╔══════════════╦════════════╦═══════════════╦══════════════╦══════════════╗
║   תאריך      ║  סכום     ║  תקופת חיוב  ║ חיובים קבועים║חיובים משתנים║
╠══════════════╬════════════╬═══════════════╬══════════════╬══════════════╣
║ DD/MM/YYYY   ║  XXX ₪     ║ MM-MM/YYYY    ║    XXX ₪     ║    XXX ₪     ║
╚══════════════╩════════════╩═══════════════╩══════════════╩══════════════╝

הנחיות נוספות:
- הצג את כל הסכומים עם הסימן ₪
- ציין שינויים משמעותיים בין חשבוניות בדגש מיוחד
- הוסף שורת סיכום בתחתית הטבלה
- מספר בשדה סכום יוצג עם 2 ספרות אחרי הנקודה העשרונית

לדוגמה:
╔══════════════╦════════════╦═══════════════╦══════════════╦══════════════╗
║   תאריך      ║   סכום    ║  תקופת חיוב  ║חיובים קבועים║חיובים משתנים║
╠══════════════╬════════════╬═══════════════╬══════════════╬══════════════╣
║ 07/02/2024   ║ 174.48 ₪  ║ 08/01-07/02   ║   169.90 ₪   ║    4.58 ₪    ║
║ 07/01/2024   ║ 174.48 ₪  ║ 08/12-07/01   ║   169.90 ₪   ║    4.58 ₪    ║
╠══════════════╬════════════╬═══════════════╬══════════════╬══════════════╣
║    סה״כ      ║ 348.96 ₪  ║      -        ║   339.80 ₪   ║    9.16 ₪    ║
╚══════════════╩════════════╩═══════════════╩══════════════╩══════════════╝
"""

        enhanced_message = f"""
{table_instructions}

שאלת המשתמש: {request.message}

מידע החשבוניות:
{chr(10).join(combined_text)}
"""


        # Check cache before saving user message
        cache_key = f"chat_cache:{hashlib.sha256(f'{request.message}:{request.customerId}'.encode()).hexdigest()}"
        cached_response = await redis_client.get(cache_key)
        is_cache_hit = bool(cached_response)

        try:
            user_message = ChatMessage(
                session_id=session['id'],
                message_type='user',
                content=request.message,
                pdf_context=current_pdf_id,
                metadata={
                    'customer_id': request.customerId,
                    'pdf_path': request.pdf_path,
                    'timestamp': datetime.utcnow().isoformat(),
                    'cache_hit': is_cache_hit
                }
            )
            await chat_history_service.save_message(user_message)
        except Exception as e:
            logger.error(f"Failed to save user message: {e}", exc_info=True)

        # Get response from cache or Claude
        if cached_response:
            logger.info("Using cached response")
            response = json.loads(cached_response)
        else:
            response = await claude_service.get_response(
                message=enhanced_message,
                pdf_content=chr(10).join(combined_text)
            )
            # Cache the response
            await redis_client.set(cache_key, json.dumps(response))
            await redis_client.expire(cache_key, 3600)  # Set TTL to 1 hour

        # Save bot response
        try:
            bot_message = ChatMessage(
                session_id=session['id'],
                message_type='bot',
                content=response,
                pdf_context=current_pdf_id,
                metadata={
                    'customer_id': request.customerId,
                    'pdf_path': request.pdf_path,
                    'timestamp': datetime.utcnow().isoformat(),
                    'cache_hit': is_cache_hit
                }
            )
            await chat_history_service.save_message(bot_message)
        except Exception as e:
            logger.error(f"Failed to save bot response: {e}", exc_info=True)

        return {
            "response": response,
            "status": "success",
            "bills_analyzed": len(combined_text),
            "session_id": str(session['id']),
            "pdf_id": str(current_pdf_id) if current_pdf_id else None,
            "cache_hit": is_cache_hit
        }

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bill-info/{customer_id}")
async def get_bill_info(request: Request, customer_id: str):
    """Get processed bill information"""
    try:
                # Get session info if needed
        session = getattr(request.state, 'session', None)
        pdfs = await pdf_service.get_customer_pdfs(customer_id)
        if not pdfs:
            raise HTTPException(status_code=404, detail="No bills found")

        first_pdf = pdfs[0]
        pdf_content = await pdf_service.extract_pdf_text(first_pdf.path)
        
        # Process bill data
        bill_data = bill_processor.process_bill(pdf_content)
        
        return {
            "status": "success",
            "data": bill_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bill-analysis/{customer_id}")
async def analyze_bill(request: Request, customer_id: str, query: Optional[str] = None):
    """Analyze specific aspects of the bill"""
    try:
        session = getattr(request.state, 'session', None)
        pdfs = await pdf_service.get_customer_pdfs(customer_id)
        if not pdfs:
            raise HTTPException(status_code=404, detail="No bills found")

        first_pdf = pdfs[0]
        pdf_content = await pdf_service.extract_pdf_text(first_pdf.path)
        
        # Process and analyze bill
        bill_data = bill_processor.process_bill(pdf_content)
        
        analysis = {
            "summary": {
                "total_amount": bill_data.get("total_amount"),
                "billing_period": bill_data.get("billing_period"),
                "phone_numbers": bill_data.get("phone_numbers", [])
            },
            "details": {
                "fixed_charges": bill_data.get("fixed_charges", []),
                "usage": bill_data.get("usage", {}),
                "plan": bill_data.get("plan", {})
            }
        }
        
        return {
            "status": "success",
            "data": analysis
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

