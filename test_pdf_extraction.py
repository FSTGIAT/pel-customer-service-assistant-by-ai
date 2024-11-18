import asyncio
from app.services.pdf_service import pdf_service
from app.services.telecom_bill_processor import bill_processor, query_processor
from app.services.claude_service import claude_service

async def test_full_flow():
    customer_id = "3694388_07012024"
    test_query = "כמה דיבר מנוי 0503060366"
    
    print("Testing full PDF-to-Answer flow...")
    
    try:
        # Step 1: Get PDF and extract text
        print("\n1. PDF Text Extraction:")
        pdfs = await pdf_service.get_customer_pdfs(customer_id)
        if not pdfs:
            print("❌ No PDFs found!")
            return
            
        pdf_text = await pdf_service.extract_pdf_text(pdfs[0]['path'])
        print(f"✅ Extracted {len(pdf_text)} characters")
        
        # Step 2: Process bill data
        print("\n2. Bill Data Processing:")
        bill_data = bill_processor.process_bill(pdf_text)
        if not bill_data:
            print("❌ Failed to process bill data!")
            return
            
        print("✅ Processed bill data:")
        for key, value in bill_data.items():
            print(f"  - {key}: {str(value)[:100]}...")
            
        # Step 3: Create prompt
        print("\n3. Prompt Creation:")
        prompt = query_processor.create_prompt(test_query, bill_data)
        print("✅ Created prompt:")
        print(prompt[:200] + "...")
        
        # Step 4: Get Claude response
        print("\n4. Claude Response:")
        response = await claude_service.get_response(
            message=test_query,
            pdf_content=pdf_text,
            system_prompt=prompt
        )
        print("\nFinal Response:")
        print("-" * 80)
        print(response)
        print("-" * 80)
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
