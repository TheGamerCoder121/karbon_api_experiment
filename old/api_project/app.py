from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Authentication
security = HTTPBearer()

KARBON_API_BASE_URL = "https://api.karbonhq.com"
KARBON_BEARER_TOKEN = os.getenv("KARBON_BEARER_TOKEN")
KARBON_ACCESS_KEY = os.getenv("KARBON_ACCESS_KEY")

async def get_karbon_api_token(credentials: HTTPAuthorizationCredentials = Depends(security), access_key: str = Header(None)):
    if credentials.credentials != KARBON_BEARER_TOKEN or access_key != KARBON_ACCESS_KEY:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return credentials.credentials

# Pydantic models for structured data
class BillingItem(BaseModel):
    id: str
    amount: float
    description: str
    date: str

class WorkItem(BaseModel):
    id: str
    title: str
    status: str
    due_date: Optional[str]

class Timesheet(BaseModel):
    id: str
    employee: str
    date: str
    hours: float
    project: str

class BudgetToActual(BaseModel):
    project: str
    budgeted_amount: float
    actual_amount: float
    variance: float

# API endpoints
@app.get("/billing", response_model=List[BillingItem])
async def get_billing(token: str = Depends(get_karbon_api_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{KARBON_API_BASE_URL}/billing", headers={"Authorization": f"Bearer {token}"})
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch billing data")
    return [BillingItem(**item) for item in response.json()]

@app.get("/work-items", response_model=List[WorkItem])
async def get_work_items(token: str = Depends(get_karbon_api_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{KARBON_API_BASE_URL}/work-items", headers={"Authorization": f"Bearer {token}"})
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch work items")
    return [WorkItem(**item) for item in response.json()]

@app.get("/timesheets", response_model=List[Timesheet])
async def get_timesheets(token: str = Depends(get_karbon_api_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{KARBON_API_BASE_URL}/timesheets", headers={"Authorization": f"Bearer {token}"})
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch timesheets")
    return [Timesheet(**item) for item in response.json()]

@app.get("/budget-to-actual", response_model=List[BudgetToActual])
async def get_budget_to_actual(token: str = Depends(get_karbon_api_token)):
    # This endpoint would typically involve more complex logic to calculate budget vs actual
    # For now, we'll return mock data
    return [
        BudgetToActual(project="Project A", budgeted_amount=10000, actual_amount=9500, variance=500),
        BudgetToActual(project="Project B", budgeted_amount=15000, actual_amount=16000, variance=-1000),
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
