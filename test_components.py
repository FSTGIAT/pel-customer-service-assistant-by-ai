import asyncio
import os
from app.services.pdf_service import pdf_service
from app.services.telecom_bill_processor import bill_processor, query_processor
from app.services.claude_service import claude_service

async def test_components():
    customer_id = "3694388_07012024"  # Your test customer ID
    
    print("1. Testing PDF Service...")
    pdfs = await pdf_service.get_customer_pdfs(customer_id)
    if pdfs:
        print(f"Found {len(pdfs)} PDFs")
        print(f"First PDF path: {pdfs[0]['path']}")
        
        # Test text extraction
        print("\n2. Testing Text Extraction...")
        pdf_text = await pdf_service.extract_pdf_text(pdfs[0]['path'])
        print(f"Extracted text sample (first 200 chars):\n{pdf_text[:200]}")
        
        # Test bill processing
        print("\n3. Testing Bill Processing...")
        bill_data = bill_processor.process_bill(pdf_text)
        print(f"Processed bill data:\n{bill_data}")
        
        # Test query processing
        print("\n4. Testing Query Processing...")
        test_query = "כמה דיבר מנוי 0503060366"
        prompt = query_processor.create_prompt(test_query, bill_data)
        print(f"Generated prompt sample:\n{prompt[:200]}")
        
        # Test Claude service
        print("\n5. Testing Claude Service...")
        response = await claude_service.get_response(
            message=test_query,
            pdf_content=pdf_text,
            system_prompt=prompt
        )
        print(f"Claude response:\n{response}")
    else:
        print("No PDFs found!")

if __name__ == "__main__":
    asyncio.run(test_components())
