from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas
from database import get_db
from models import ConsumptionProduction, Customer, SIPXPrice
from datetime import datetime

router = APIRouter(
    prefix="/consumption-production",
    tags=["Consumption production"]
)

# add consumption-production data to customer
@router.post("/", response_model=schemas.ConsumptionProduction)
def create_consumption_production(data: schemas.ConsumptionProductionCreate, db: Session = Depends(get_db)):
  # Ensure customer exists before inserting contuption-production data
  customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
  if not customer:
    raise HTTPException(status_code=400, detail="Customer does not exist")

  # Ensure that the customer doesn't already have consumption-production data
  # at given timestamp
  consumption_production_data = (
    db.query(ConsumptionProduction)
    .filter(ConsumptionProduction.customer_id == data.customer_id)
    .filter(ConsumptionProduction.timestamp == data.timestamp)
    .first())

  # If data already exists raise an error 
  if consumption_production_data:
    raise HTTPException(status_code=409, detail="Data already exists")

  # Add consumption-production data
  time_series_entry = ConsumptionProduction(**data.model_dump())
  db.add(time_series_entry)
  db.commit()
  db.refresh(time_series_entry)

  return time_series_entry

# gets all consumption and production data for customer
@router.get("/{customer_id}", response_model=list[schemas.ConsumptionProduction])
def get_consumption_production_all(customer_id: int, db: Session = Depends(get_db)):
  data = db.query(ConsumptionProduction).filter(ConsumptionProduction.customer_id == customer_id).all()
  # if data doesn't exist raise error
  if not data:
    raise HTTPException(status_code=404, detail="No data found for customer")
  return data

# get constumption and production data for a customer in a given range
@router.get("/{customer_id}/range", response_model=list[schemas.ConsumptionProduction])
def get_consumption_data(customer_id: int, start: datetime, end: datetime, db: Session = Depends(get_db)):
  data = db.query(ConsumptionProduction).filter(
    ConsumptionProduction.customer_id == customer_id,
    ConsumptionProduction.timestamp >= start,
    ConsumptionProduction.timestamp <= end
  ).all()

  # if data doesn't exist raise error
  if not data: 
    raise HTTPException(status_code=404, detail="No data found for customer")
  
  return data

# calculates the total revenue and cost of a customer in a given range
@router.get("/{customer_id}/total", response_model=schemas.CostRevenueSummary)
def calculate_cost_revenue(customer_id: int, start: datetime, end: datetime, db: Session = Depends(get_db)):
  data = get_consumption_data(customer_id, start, end, db)
  prices = db.query(SIPXPrice).filter(
    SIPXPrice.timestamp.between(start, end)
  ).all()
  price_map = {price.timestamp: price.price_EUR_kWh for price in prices}

  # calculates the cost and revenue
  total_cost = sum(d.consumption_kWh * price_map[d.timestamp] for d in data if d.consumption_kWh)
  total_revenue = sum(d.production_kWh * price_map[d.timestamp] for d in data if d.production_kWh)

  return {"total_cost": total_cost, "total_revenue": total_revenue}

# updates a consumption-production entry
@router.patch("/{entry_id}", response_model=schemas.ConsumptionProductionUpdate)
def update_consumption_production(entry_id: int, update_data: schemas.ConsumptionProductionUpdate, db: Session = Depends(get_db)):
  entry = db.query(ConsumptionProduction).filter(ConsumptionProduction.id == entry_id).first()
    
  if not entry:
    raise HTTPException(status_code=404, detail="Consumption-Production entry not found")

  if update_data.consumption_kWh is not None:
    entry.consumption_kWh = update_data.consumption_kWh

  if update_data.production_kWh is not None:
    entry.production_kWh = update_data.production_kWh

  db.commit()
  db.refresh(entry)
  return entry
