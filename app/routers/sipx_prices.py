from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db 
import schemas
import json
import redis
from redis_client import get_redis_client
from datetime import datetime
from models import SIPXPrice
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
  prefix="/sipx-prices",
  tags=["Sipx prices"]
)

# creates new entry with price and timestamp
@router.post("/", response_model=schemas.SIPXPrice)
@limiter.limit("20/minute")
async def create_price_entry(request: Request, data: schemas.SIPXPriceCreate, db: AsyncSession = Depends(get_db)):
  # Check if a price entry already exists for the given timestamp
  result = await db.execute(select(SIPXPrice).filter(SIPXPrice.timestamp == data.timestamp))
  existing_entry = result.scalars().first()

  if existing_entry:
    # Optionally, update the existing entry or raise an error
    raise HTTPException(status_code=400, detail="Price entry for this timestamp already exists")
  
  price_entry = SIPXPrice(**data.model_dump())
  db.add(price_entry)
  await db.commit()  # Async commit
  await db.refresh(price_entry)  # Async refresh
  return price_entry

# gets all prices
@router.get("/", response_model=list[schemas.SIPXPrice])
@limiter.limit("20/minute")
async def get_all_prices(request: Request, redis: redis.Redis = Depends(get_redis_client), db: AsyncSession = Depends(get_db)):

  cached_data = redis.get("spix_prices")

  if cached_data:
    return json.loads(cached_data)

  result = await db.execute(select(SIPXPrice))
  data = result.scalars().all()

  redis.set("spix_prices", json.dumps([price.to_dict() for price in data]), ex=360) 

  return data

# gets a range of prices from start to end
@router.get("/range", response_model=list[schemas.SIPXPrice])
@limiter.limit("20/minute")
async def get_prices_in_range(request: Request, start: datetime, end: datetime, db: AsyncSession = Depends(get_db)):
  result = await db.execute(select(SIPXPrice).filter(
    SIPXPrice.timestamp >= start,
    SIPXPrice.timestamp <= end
  ))
  data = result.scalars().all()
  
  # If data doesn't exist, raise an error
  if not data:
    raise HTTPException(status_code=404, detail="No data found in the given range")
  
  return data

# gets the latest entry
@router.get("/latest", response_model=schemas.SIPXPrice)
@limiter.limit("20/minute")
async def get_latest_price(request: Request, db: AsyncSession = Depends(get_db)):
  result = await db.execute(select(SIPXPrice).order_by(SIPXPrice.timestamp.desc()))
  latest_entry = result.scalars().first()

  if not latest_entry:
    raise HTTPException(status_code=404, detail="No prices available")

  return latest_entry

# modifies the price of an entry
@router.patch("/{price_id}", response_model=schemas.SIPXPriceUpdate)
@limiter.limit("20/minute")
async def update_sipx_price(request: Request, price_id: int, update_data: schemas.SIPXPriceUpdate, db: AsyncSession = Depends(get_db)):
  result = await db.execute(select(SIPXPrice).filter(SIPXPrice.id == price_id))
  price_entry = result.scalars().first()
  
  if not price_entry:
    raise HTTPException(status_code=404, detail="SIPX price not found")
  
  if update_data.price_EUR_kWh is not None:
    price_entry.price_EUR_kWh = update_data.price_EUR_kWh

  await db.commit()  # Async commit
  await db.refresh(price_entry)  # Async refresh

  return price_entry
