from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()

class CustomerResponse(BaseModel):
    id: str
    name: str
    plan: str = "Standard"
    registerDate: Optional[datetime] = None

# Mock customer data - replace with your database later
MOCK_CUSTOMERS = {
    "3694388_07012024": {
        "id": "3694388_07012024",
        "name": "John Doe",
        "plan": "Premium",
        "registerDate": datetime.now()
    }
}

@router.get("/customer/{customer_id}")
async def get_customer(customer_id: str):
    try:
        # First try exact match
        if customer_id in MOCK_CUSTOMERS:
            return MOCK_CUSTOMERS[customer_id]
            
        # If not found, try matching just the customer number
        customer_base = customer_id.split('_')[0] if '_' in customer_id else customer_id
        
        # Look for any customer entry starting with this base number
        for cust_id, customer in MOCK_CUSTOMERS.items():
            if cust_id.startswith(customer_base):
                return customer
                
        raise HTTPException(
            status_code=404,
            detail=f"Customer not found: {customer_id}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving customer information: {str(e)}"
        )
