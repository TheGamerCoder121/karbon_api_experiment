from fastapi import FastAPI, HTTPException, Depends, Query, Security, Header
from fastapi.security import HTTPBearer, APIKeyHeader
from typing import List, Optional
from datetime import date
import httpx
import logging
from pydantic import BaseModel
from config import KARBON_BEARER_TOKEN, KARBON_ACCESS_KEY, KARBON_API_BASE_URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print(f"KARBON_BEARER_TOKEN: {KARBON_BEARER_TOKEN}")
print(f"KARBON_ACCESS_KEY: {KARBON_ACCESS_KEY}")

app = FastAPI()

security = HTTPBearer()
api_key_header = APIKeyHeader(name="AccessKey", auto_error=False)

DEBUG_MODE = False  # Set to False to enable authentication checks

class BillingItem(BaseModel):
    id: str
    amount: float
    date: date
    description: str

class WorkItem(BaseModel):
    id: str
    name: str
    status: str
    budgeted_hours: float
    actual_hours: float

class TimeEntry(BaseModel):
    id: str
    work_item_id: str
    hours: float
    date: date
    user: str

class BudgetToActualReport(BaseModel):
    work_item: WorkItem
    time_entries: List[TimeEntry]
    total_actual_hours: float
    budget_variance: float

def get_mock_billing_data():
    return [
        BillingItem(id="1", amount=100.0, date=date(2023, 1, 15), description="Invoice 1"),
        BillingItem(id="2", amount=200.0, date=date(2023, 2, 15), description="Invoice 2"),
    ]

def get_mock_work_items():
    return [
        WorkItem(id="1", name="Project A", status="in_progress", budgeted_hours=100.0, actual_hours=80.0),
        WorkItem(id="2", name="Project B", status="completed", budgeted_hours=50.0, actual_hours=55.0),
    ]

def get_mock_time_entries():
    return [
        TimeEntry(id="1", work_item_id="1", hours=8.0, date=date(2023, 1, 15), user="John Doe"),
        TimeEntry(id="2", work_item_id="1", hours=7.5, date=date(2023, 1, 16), user="Jane Smith"),
        TimeEntry(id="3", work_item_id="2", hours=6.0, date=date(2023, 2, 1), user="John Doe"),
    ]

async def get_karbon_data(endpoint: str, params: dict = None, headers: dict = None):
    if DEBUG_MODE:
        logger.info(f"Debug mode: Returning mock data for endpoint {endpoint}")
        if endpoint == "/v3/billing":
            return get_mock_billing_data()
        elif endpoint == "/v3/work":
            return get_mock_work_items()
        elif endpoint == "/v3/timesheets":
            return get_mock_time_entries()
        else:
            raise HTTPException(status_code=404, detail="Endpoint not found")

    async with httpx.AsyncClient() as client:
        if headers is None:
            headers = {}
        headers.update({
            "Authorization": f"Bearer {KARBON_BEARER_TOKEN}",
            "AccessKey": KARBON_ACCESS_KEY
        })
        try:
            logger.info(f"Sending request to Karbon API: {KARBON_API_BASE_URL}{endpoint}")
            response = await client.get(f"{KARBON_API_BASE_URL}{endpoint}", headers=headers, params=params)
            logger.info(f"Received response from Karbon API. Status code: {response.status_code}")

            if response.status_code == 200:
                logger.info(f"Successfully fetched data from {endpoint}")
                return response.json()
            elif response.status_code == 401:
                logger.error("Unauthorized access to Karbon API")
                raise HTTPException(status_code=401, detail="Unauthorized access to Karbon API")
            elif response.status_code == 404:
                logger.error(f"Endpoint {endpoint} not found in Karbon API")
                raise HTTPException(status_code=404, detail=f"Endpoint {endpoint} not found in Karbon API")
            else:
                logger.error(f"Unexpected status code {response.status_code} from Karbon API")
                return get_mock_billing_data()  # Return mock data for testing purposes
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            return get_mock_billing_data()  # Return mock data for testing purposes
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return get_mock_billing_data()  # Return mock data for testing purposes

async def authenticate(authorization: str = Header(None), access_key: str = Header(None, alias="AccessKey")):
    logger.info("Starting authentication process")
    logger.info(f"Received headers: {dict(authorization=authorization, AccessKey=access_key)}")
    logger.info(f"Expected Bearer Token: {KARBON_BEARER_TOKEN}")
    logger.info(f"Expected Access Key: {KARBON_ACCESS_KEY}")

    if DEBUG_MODE:
        logger.info("Debug mode active, skipping authentication")
        return True

    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not access_key:
        logger.warning("Missing AccessKey header")
        raise HTTPException(status_code=401, detail="Missing AccessKey header")

    logger.info("Validating Authorization header format")
    if not authorization.startswith("Bearer "):
        logger.warning("Invalid Authorization header format")
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    token = authorization.split(" ")[1]
    logger.info("Extracted Bearer token")

    logger.info("Validating Bearer token")
    if token != KARBON_BEARER_TOKEN:
        logger.warning("Invalid Bearer token")
        raise HTTPException(status_code=401, detail="Invalid Bearer token")

    logger.info("Validating Access Key")
    if access_key != KARBON_ACCESS_KEY:
        logger.warning("Invalid Access Key")
        raise HTTPException(status_code=401, detail="Invalid Access Key")

    logger.info("Authentication successful")
    return True

@app.get("/api/billing", response_model=List[BillingItem])
async def get_billing_data(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    authenticated: bool = Depends(authenticate)
):
    logger.info(f"Received request for billing data: start_date={start_date}, end_date={end_date}")
    params = {}
    if start_date:
        params['startDate'] = start_date.isoformat()
    if end_date:
        params['endDate'] = end_date.isoformat()
    return await get_karbon_data("/v3/billing", params)

@app.get("/api/work-items", response_model=List[WorkItem])
async def get_work_items(
    status: Optional[str] = Query(None),
    authenticated: bool = Depends(authenticate)
):
    logger.info(f"Received request for work items: status={status}")
    params = {'status': status} if status else {}
    return await get_karbon_data("/v3/WorkItems", params)

@app.get("/api/timesheets", response_model=List[TimeEntry])
async def get_timesheets(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    authenticated: bool = Depends(authenticate)
):
    logger.info(f"Received request for timesheets: start_date={start_date}, end_date={end_date}")
    params = {}
    if start_date:
        params['startDate'] = start_date.isoformat()
    if end_date:
        params['endDate'] = end_date.isoformat()
    return await get_karbon_data("/v3/timesheets", params)

@app.get("/api/budget-to-actual", response_model=List[BudgetToActualReport])
async def get_budget_to_actual(
    start_date: date = Query(...),
    end_date: date = Query(...),
    authenticated: bool = Depends(authenticate)
):
    logger.info(f"Received request for budget-to-actual report: start_date={start_date}, end_date={end_date}")
    work_items = await get_work_items()
    timesheets = await get_timesheets(start_date=start_date, end_date=end_date)

    reports = []
    for work_item in work_items:
        related_time_entries = [entry for entry in timesheets if entry.work_item_id == work_item.id]
        total_actual_hours = sum(entry.hours for entry in related_time_entries)
        budget_variance = work_item.budgeted_hours - total_actual_hours

        reports.append(BudgetToActualReport(
            work_item=work_item,
            time_entries=related_time_entries,
            total_actual_hours=total_actual_hours,
            budget_variance=budget_variance
        ))

    return reports

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
