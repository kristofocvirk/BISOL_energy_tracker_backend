from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import schemas 
from datetime import datetime
from models import SIPXPrice

router = APIRouter(
  prefix="/sipx-prices",
  tags=["Sipx prices"]
)

@router.post("/", response_model=schemas.SIPXPrice)
def create_price_entry(data: schemas.SIPXPriceCreate, db: Session = Depends(get_db)):
  price_entry = SIPXPrice(**data.model_dump())
  db.add(price_entry)
  db.commit()
  db.refresh(price_entry)
  return price_entry

@router.get("/", response_model=list[schemas.SIPXPrice])
def get_all_prices(db: Session = Depends(get_db)):
  return db.query(SIPXPrice).all()

@router.get("/range", response_model=list[schemas.SIPXPrice])
def get_prices_in_range(start: datetime, end: datetime, db: Session = Depends(get_db)):
  data = db.query(SIPXPrice).filter(
    SIPXPrice.timestamp >= start,
    SIPXPrice.timestamp <= end
  ).all()
    
  if not data:
    raise HTTPException(status_code=404, detail="No data found in the given range")
    
  return data

@router.get("/latest", response_model=schemas.SIPXPrice)
def get_latest_price(db: Session = Depends(get_db)):
  latest_entry = db.query(SIPXPrice).order_by(SIPXPrice.timestamp.desc()).first()
    
  if not latest_entry:
    raise HTTPException(status_code=404, detail="No prices available")
    
  return latest_entry

@router.patch("/{price_id}", response_model=schemas.SIPXPriceUpdate)
def update_sipx_price(price_id: int, update_data: schemas.SIPXPriceUpdate, db: Session = Depends(get_db)):
  price_entry = db.query(SIPXPrice).filter(SIPXPrice.id == price_id).first()
  
  if not price_entry:
    raise HTTPException(status_code=404, detail="SIPX price not found")
    
  if update_data.price_EUR_kWh is not None:
    price_entry.price_EUR_kWh = update_data.price_EUR_kWh

  db.commit()
  db.refresh(price_entry)
  return price_entry