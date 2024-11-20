from fastapi import APIRouter, HTTPException, Request
from typing import Optional, List
from pydantic import BaseModel
from app.services.claude_service import claude_service
from app.services.pdf_service import pdf_service
from app.services.telecom_bill_processor import bill_processor, query_processor
import logging
from dataclasses import asdict

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

@router.post("/chat")
async def chat(request: ChatRequest, req: Request):  # Add req: Request
    """Handle chat requests with beautified table formatting"""
    try:
                # Get session info if needed
        session = getattr(req.state, 'session', None)
        
        pdfs = await pdf_service.get_customer_pdfs(request.customerId)
        if not pdfs:
            raise HTTPException(status_code=404, detail="No bills found")

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

        response = await claude_service.get_response(
            message=enhanced_message,
            pdf_content=chr(10).join(combined_text)
        )

        return {
            "response": response,
            "status": "success",
            "bills_analyzed": len(combined_text)
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