from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..database import get_db 
import app.schemas as schemas
import json
import redis
from app.redis_client import get_redis_client
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.models import ConsumptionProduction, Customer, SIPXPrice
from datetime import datetime

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
  prefix="/consumption-production",
  tags=["Consumption production"]
)

# add consumption-production data to customer
@router.post("/", response_model=schemas.ConsumptionProduction)
@limiter.limit("20/minute")
async def create_consumption_production(request: Request, data: schemas.ConsumptionProductionCreate, db: AsyncSession = Depends(get_db)):
  # Ensure customer exists before inserting consumption-production data
  result = await db.execute(select(Customer).filter(Customer.id == data.customer_id))
  customer = result.scalars().first()
  if not customer:
    raise HTTPException(status_code=400, detail="Customer does not exist")

  # Ensure that the customer doesn't already have consumption-production data at the given timestamp
  result = await db.execute(select(ConsumptionProduction).filter(
    ConsumptionProduction.customer_id == data.customer_id,
    ConsumptionProduction.timestamp == data.timestamp
  ))
  consumption_production_data = result.scalars().first()

  # If data already exists, raise an error 
  if consumption_production_data:
    raise HTTPException(status_code=409, detail="Data already exists")

  # Add consumption-production data
  time_series_entry = ConsumptionProduction(**data.model_dump())
  db.add(time_series_entry)
  await db.commit()  # Async commit
  await db.refresh(time_series_entry)  # Async refresh

  return time_series_entry

# gets all consumption and production data for customer
@router.get("/{customer_id}", response_model=list[schemas.ConsumptionProduction])
@limiter.limit("20/minute")
async def get_consumption_production_all(request: Request, customer_id: int, redis: redis.Redis = Depends(get_redis_client), db: AsyncSession = Depends(get_db)):
  redis_name = f"customer_{customer_id}_production_consumption"
  cached_data = redis.get(redis_name) 

  if cached_data:
    return json.loads(cached_data)

  result = await db.execute(select(ConsumptionProduction).filter(ConsumptionProduction.customer_id == customer_id))
  data = result.scalars().all()
  if not data:
    raise HTTPException(status_code=404, detail="No data found for customer")

  redis.set(redis_name, json.dumps([price.to_dict() for price in data]), ex=360)
  return data

# get consumption and production data for a customer in a given range
@router.get("/{customer_id}/range", response_model=list[schemas.ConsumptionProduction])
@limiter.limit("20/minute")
async def get_consumption_data(request: Request, customer_id: int, start: datetime, end: datetime, db: AsyncSession = Depends(get_db)):
  result = await db.execute(select(ConsumptionProduction).filter(
    ConsumptionProduction.customer_id == customer_id,
    ConsumptionProduction.timestamp >= start,
    ConsumptionProduction.timestamp <= end
  ))
  data = result.scalars().all()
  if not data: 
    raise HTTPException(status_code=404, detail="No data found for customer")
  return data

# calculates the total revenue and cost of a customer in a given range
@router.get("/{customer_id}/total", response_model=schemas.CostRevenueSummary)
@limiter.limit("20/minute")
async def calculate_cost_revenue(request: Request, customer_id: int, start: datetime, end: datetime, db: AsyncSession = Depends(get_db)):
  data = await get_consumption_data(customer_id, start, end, db)  # Use the async version of get_consumption_data
  result = await db.execute(select(SIPXPrice).filter(SIPXPrice.timestamp.between(start, end)))
  prices = result.scalars().all()
  price_map = {price.timestamp: price.price_EUR_kWh for price in prices}

  # calculates the cost and revenue
  total_cost = sum(d.consumption_kWh * price_map[d.timestamp] for d in data if d.consumption_kWh)
  total_revenue = sum(d.production_kWh * price_map[d.timestamp] for d in data if d.production_kWh)

  return {"total_cost": total_cost, "total_revenue": total_revenue}

# updates a consumption-production entry
@router.patch("/{entry_id}", response_model=schemas.ConsumptionProductionUpdate)
@limiter.limit("20/minute")
async def update_consumption_production(request: Request, entry_id: int, update_data: schemas.ConsumptionProductionUpdate, db: AsyncSession = Depends(get_db)):
  result = await db.execute(select(ConsumptionProduction).filter(ConsumptionProduction.id == entry_id))
  entry = result.scalars().first()

  if not entry:
    raise HTTPException(status_code=404, detail="Consumption-Production entry not found")

  if update_data.consumption_kWh is not None:
    entry.consumption_kWh = update_data.consumption_kWh

  if update_data.production_kWh is not None:
    entry.production_kWh = update_data.production_kWh

  await db.commit()  # Async commit
  await db.refresh(entry)  # Async refresh
  return entry

