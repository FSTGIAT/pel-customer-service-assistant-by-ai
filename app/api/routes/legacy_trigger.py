from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import logging
from app.services.pdf_service import pdf_service
from dataclasses import asdict

router = APIRouter()
logger = logging.getLogger(__name__)

class LegacyTriggerRequest(BaseModel):
    customer_id: str

class LegacyTriggerResponse(BaseModel):
    status: str = "success"
    customer_id: str
    pdf_files: List[Dict]
    error: Optional[str] = None

@router.post("/legacy/trigger")
async def handle_legacy_trigger(request: LegacyTriggerRequest):
    """Handle legacy system trigger and return PDF list"""
    try:
        # Get PDFs using the same pattern as chat endpoint
        pdfs = await pdf_service.get_customer_pdfs(request.customer_id)
        if not pdfs:
            raise HTTPException(status_code=404, detail="No bills found")

        # Convert PDFMetadata objects to dictionaries
        pdf_dicts = [asdict(pdf) for pdf in pdfs]

        # Format response using the dictionary data
        formatted_files = [{
            "path": pdf['path'],
            "name": pdf['name'],
            "url": f"/api/pdf/view/{pdf['name']}",
            "date": pdf['date'].isoformat() if pdf['date'] else None,
            "pages": pdf.get('pages', 0)
        } for pdf in pdf_dicts]

        return {
            "status": "success",
            "customer_id": request.customer_id.split('_')[0],
            "pdf_files": formatted_files
        }

    except Exception as e:
        logger.error(f"Error in legacy trigger endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pdf/view/{filename}")
async def get_pdf(filename: str):
    """Serve PDF file"""
    try:
        pdf_path = os.path.join(pdf_service.base_directory, filename)
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="PDF file not found")
            
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=filename
        )
    except Exception as e:
        logger.error(f"Error serving PDF {filename}: {str(e)}")
        raise HTTPException(status_code=404, detail="PDF not found")

@router.get("/pdf/info/{customer_id}/{filename}")
async def get_pdf_info(customer_id: str, filename: str):
    """Get PDF metadata and content information"""
    try:
        file_path = os.path.join(pdf_service.base_directory, filename)
        pdf_info = await pdf_service.get_pdf_info(file_path)
        
        return {
            "status": "success",
            "customer_id": customer_id,
            "filename": filename,
            "pages": pdf_info["pages"],
            "text_sample": pdf_info["text_sample"]
        }
    except Exception as e:
        logger.error(f"Error getting PDF info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pdf/text/{filename}")
async def get_pdf_text(filename: str, page: Optional[int] = None):
    """Get text content from PDF, optionally from a specific page"""
    try:
        file_path = os.path.join(pdf_service.base_directory, filename)
        text_content = await pdf_service.extract_pdf_text(file_path, page)
        
        return {
            "status": "success",
            "filename": filename,
            "page": page,
            "content": text_content
        }
    except Exception as e:
        logger.error(f"Error extracting PDF text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))