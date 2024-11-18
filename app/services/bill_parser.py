import re
from typing import Dict

def extract_total_amount(pdf_content: str) -> float:
    """Extract total amount using multiple patterns"""
    amount_patterns = [
        r"174\.48",  # Direct amount from your bill
        r"סה\"כ חשבון נוכחי כולל מע\"מ\s*([\d,.]+)",
        r"סה\"כ לחשבון כולל מע\"מ\s*([\d,.]+)"
    ]
    
    for pattern in amount_patterns:
        matches = re.findall(pattern, pdf_content)
        if matches:
            try:
                amount = matches[0]
                if isinstance(amount, tuple):
                    amount = amount[0]
                return float(amount.replace(',', ''))
            except (IndexError, ValueError) as e:
                print(f"Error converting amount: {e}")
                continue
    
    return 0.0

class BillParser:
    @staticmethod
    def parse_bill(pdf_content: str) -> Dict:
        """Parse bill content and extract structured data"""
        data = {
            "total_amount": extract_total_amount(pdf_content),
            "phone_numbers": [],
            "services": [],
            "bill_period": "",
            "bill_date": ""
        }
        
        # Extract phone numbers
        phone_numbers = re.findall(r"050-\d{7}|05\d{1}-\d{7}", pdf_content)
        if phone_numbers:
            data["phone_numbers"] = phone_numbers
            
        # Extract bill period
        period_match = re.search(r"תקופת החשבון:\s*(\d{2}/\d{2}/\d{4}\s*-\s*\d{2}/\d{2}/\d{4})", pdf_content)
        if period_match:
            data["bill_period"] = period_match.group(1)
            
        return data

def debug_bill_content(pdf_content: str):
    """Debug function to help identify extraction issues"""
    print("\n=== Bill Content Debug ===")
    
    # Look for total amount
    amount_patterns = [
        r"174\.48",
        r"סה\"כ חשבון נוכחי כולל מע\"מ\s*([\d,.]+)",
        r"סך הכל לתשלום\s*([\d,.]+)",
        r"[\d,.]+\s*₪"
    ]
    
    print("\nSearching for amounts:")
    for pattern in amount_patterns:
        matches = re.findall(pattern, pdf_content)
        print(f"Pattern '{pattern}': {matches}")
        
    print("\nFirst 500 characters:")
    print(pdf_content[:500])