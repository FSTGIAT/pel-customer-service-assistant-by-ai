# test_pdf_service.py
import asyncio
from app.services.pdf_service import pdf_service

import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from app.core.database import db

async def test_pdf_operations():
    try:
        # Test customer PDFs retrieval
        customer_id = "3694388"
        print(f"\nTesting PDF retrieval for customer {customer_id}")
        pdfs = await pdf_service.get_customer_pdfs(customer_id)
        print(f"Found {len(pdfs)} PDFs")
        
        if pdfs:
            # Test text extraction
            first_pdf = pdfs[0]
            print(f"\nTesting text extraction from {first_pdf.name}")
            text = await pdf_service.extract_pdf_text(first_pdf.path)
            print(f"Extracted text length: {len(text)} characters")
            print("First 200 characters:", text[:200])
            
            # Test cached retrieval
            print("\nTesting cached retrieval")
            cached_text = await pdf_service.extract_pdf_text(first_pdf.path)
            print("Cache hit successful" if len(cached_text) == len(text) else "Cache miss")

    except Exception as e:
        print(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_pdf_operations())