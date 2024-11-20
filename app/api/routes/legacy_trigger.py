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
        logger.info(f"Processing legacy trigger for customer: {request.customer_id}")
        
        # Get PDFs using PDF service
        pdfs = await pdf_service.get_customer_pdfs(request.customer_id)
        
        if not pdfs:
            logger.warning(f"No PDFs found for customer {request.customer_id}")
            return {
                "status": "success",
                "customer_id": request.customer_id,
                "pdf_files": []
            }

        # Convert PDFMetadata objects to dictionaries with error handling
        formatted_files = []
        for pdf in pdfs:
            try:
                pdf_dict = {
                    "path": pdf.path,
                    "name": pdf.name,
                    "url": f"/api/pdf/view/{pdf.name}",
                    "pages": pdf.pages,
                    "date": pdf.date.isoformat() if pdf.date else None,
                }
                formatted_files.append(pdf_dict)
            except AttributeError as e:
                logger.error(f"Error formatting PDF metadata: {str(e)}")
                continue

        response_data = {
            "status": "success",
            "customer_id": request.customer_id.split('_')[0],
            "pdf_files": formatted_files
        }

        logger.info(f"Successfully processed legacy trigger. Found {len(formatted_files)} PDFs")
        return response_data

    except Exception as e:
        logger.error(f"Error in legacy trigger endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/pdf/view/{filename}")
async def get_pdf(filename: str):
    """Serve PDF file"""
    try:
        pdf_path = os.path.join(pdf_service.base_directory, filename)
        
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {filename}")
            raise HTTPException(status_code=404, detail="PDF file not found")
        
        logger.info(f"Serving PDF file: {filename}")
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
        metadata = await pdf_service.get_pdf_metadata(file_path)
        
        return {
            "status": "success",
            "customer_id": customer_id,
            "filename": filename,
            "pages": metadata.get("pages", 0),
            "size": metadata.get("size", 0),
            "date": metadata.get("date"),
            "is_valid": metadata.get("is_valid", False)
        }
    except Exception as e:
        logger.error(f"Error getting PDF info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))