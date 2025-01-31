from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db  # Ensure get_db is now async
import schemas
from datetime import datetime
from models import SIPXPrice

router = APIRouter(
  prefix="/sipx-prices",
  tags=["Sipx prices"]
)

# creates new entry with price and timestamp
@router.post("/", response_model=schemas.SIPXPrice)
async def create_price_entry(data: schemas.SIPXPriceCreate, db: AsyncSession = Depends(get_db)):
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
async def get_all_prices(db: AsyncSession = Depends(get_db)):
  result = await db.execute(select(SIPXPrice))
  data = result.scalars().all()
  return data

# gets a range of prices from start to end
@router.get("/range", response_model=list[schemas.SIPXPrice])
async def get_prices_in_range(start: datetime, end: datetime, db: AsyncSession = Depends(get_db)):
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
async def get_latest_price(db: AsyncSession = Depends(get_db)):
  result = await db.execute(select(SIPXPrice).order_by(SIPXPrice.timestamp.desc()))
  latest_entry = result.scalars().first()

  if not latest_entry:
    raise HTTPException(status_code=404, detail="No prices available")

  return latest_entry

# modifies the price of an entry
@router.patch("/{price_id}", response_model=schemas.SIPXPriceUpdate)
async def update_sipx_price(price_id: int, update_data: schemas.SIPXPriceUpdate, db: AsyncSession = Depends(get_db)):
  result = await db.execute(select(SIPXPrice).filter(SIPXPrice.id == price_id))
  price_entry = result.scalars().first()
  
  if not price_entry:
    raise HTTPException(status_code=404, detail="SIPX price not found")
  
  if update_data.price_EUR_kWh is not None:
    price_entry.price_EUR_kWh = update_data.price_EUR_kWh

  await db.commit()  # Async commit
  await db.refresh(price_entry)  # Async refresh

  return price_entry
