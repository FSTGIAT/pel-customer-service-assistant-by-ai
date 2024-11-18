from fastapi import APIRouter, HTTPException
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
async def chat(request: ChatRequest):
    """Handle chat requests by sending PDF text directly to Claude"""
    try:
        # Get PDFs
        pdfs = await pdf_service.get_customer_pdfs(request.customerId)
        if not pdfs:
            raise HTTPException(status_code=404, detail="No bills found")

        # Access the first PDF's path using property notation
        first_pdf = pdfs[0]  # Get first PDFMetadata object
        pdf_path = first_pdf.path  # Access path attribute directly

        # Get the text content only once
        pdf_text = await pdf_service.extract_pdf_text(pdf_path)
        if not pdf_text:
            raise HTTPException(status_code=500, detail="Could not read bill content")

        # Send directly to Claude with the text
        response = await claude_service.get_response(
            message=request.message,
            pdf_content=pdf_text  # Just passing the text
        )

        return {
            "response": response,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bill-info/{customer_id}")
async def get_bill_info(customer_id: str):
    """Get processed bill information"""
    try:
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
async def analyze_bill(customer_id: str, query: Optional[str] = None):
    """Analyze specific aspects of the bill"""
    try:
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