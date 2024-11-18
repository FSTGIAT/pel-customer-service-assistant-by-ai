import pytest
import asyncio
from app.services.telecom_bill_processor import bill_processor
from app.services.claude_service import claude_service

# Updated sample bill with correct section markers
SAMPLE_BILL = """סיכום החשבון שלך בהתייחס למנויים שברשותך:
050-5148080, 050-3060366

חיובים קבועים למנוי
-------------------
שירות תיקונים פלאפון Top למספר אלקטרוני 352680946299313 39.90 39.90
שירות תיקונים פלאפון למספר אלקטרוני 358779103142227 39.90 39.90

חיובים משתנים
-------------
0.00

סה"כ חשבון נוכחי כולל מע"מ 174.48 ₪
תקופת החשבון: 08/09/2024 - 07/10/2024

צריכת דקות והודעות SMS שבוצעו בארץ
----------------------------------
0503060366 שיחות 247:54 710:37 73:11 1031:42
SMS/MMS 0 6 0 6
0505148080 שיחות 399:49 34:35 0:00 434:24

שיעור שימוש בחבילות
------------------
0503060366 דקות שיחה 2500:00 1025:47 41%
0503060366 גלישה באינטרנט בארץ(ב-MB) 102400 1670.306 2%"""

def test_bill_processor():
    """Test basic bill processing"""
    bill_data = bill_processor.process_bill(SAMPLE_BILL)
    
    # Print debug info
    print("\nProcessed bill data:", bill_data)
    
    # Basic assertions
    assert bill_data["total_amount"] == 174.48, "Wrong total amount"
    assert "050-5148080" in bill_data["phones"], "Missing phone number"
    assert "050-3060366" in bill_data["phones"], "Missing phone number"
    
    # Check service charges
    charges = bill_data.get("charges", {})
    assert charges.get("repairs_top", 0) == 39.90, f"Wrong repair service amount. Got: {charges}"
    assert charges.get("repairs_regular", 0) == 39.90, "Wrong regular repair service amount"
    
    print("✓ Bill processor test passed")

@pytest.mark.asyncio
async def test_amount_query():
    """Test total amount query"""
    response = await claude_service.get_response(
        message="כמה הסכום לתשלום?",
        pdf_content=SAMPLE_BILL
    )
    
    print("\nAmount query response:", response)
    
    assert "174.48" in response, "Amount not found in response"
    assert "₪" in response, "Currency symbol missing"
    assert "503060366" not in response, "Phone number incorrectly interpreted as amount"
    
    print("✓ Amount query test passed")

@pytest.mark.asyncio
async def test_service_query():
    """Test service charges query"""
    response = await claude_service.get_response(
        message="כמה עולה שירות תיקונים?",
        pdf_content=SAMPLE_BILL
    )
    
    print("\nService query response:", response)
    
    assert any(x in response for x in ["39.90", "39.9"]), "Service charge amount not found"
    assert "תיקונים" in response, "Service name not found"
    assert "Top" in response, "Service type not found"
    
    print("✓ Service query test passed")

# Add debugging function
def debug_bill_processing(bill_content: str):
    """Debug bill processing"""
    print("\nDebugging bill processing:")
    bill_data = bill_processor.process_bill(bill_content)
    
    print("\nExtracted sections:")
    for section_name, section in bill_processor.sections.items():
        print(f"\n{section_name}:")
        print("-" * 40)
        print(section.content)
    
    print("\nExtracted data:")
    print(f"Total amount: {bill_data.get('total_amount')}")
    print(f"Billing period: {bill_data.get('billing_period')}")
    print(f"Phone numbers: {bill_data.get('phones')}")
    print(f"Service charges: {bill_data.get('charges')}")
    
    return bill_data

if __name__ == "__main__":
    # Debug bill processing
    debug_bill_processing(SAMPLE_BILL)
    
    # Run tests
    pytest.main(["-v", __file__])
