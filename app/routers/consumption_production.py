from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import schemas
from database import get_db
from models import ConsumptionProduction, Customer
from datetime import datetime

router = APIRouter(
    prefix="/consumption-production",
    tags=["Consumption production"]
)

# stranki doda časovno vrsto
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

    if consumption_production_data:
        raise HTTPException(status_code=409, detail="Data already exists")

    time_series_entry = ConsumptionProduction(**data.model_dump())
    db.add(time_series_entry)
    db.commit()
    db.refresh(time_series_entry)
    return time_series_entry

@router.get("/{customer_id}", response_model=list[schemas.ConsumptionProduction])
def get_time_series(customer_id: int, db: Session = Depends(get_db)):
    data = db.query(ConsumptionProduction).filter(ConsumptionProduction.customer_id == customer_id).all()
    if not data:
        raise HTTPException(status_code=404, detail="No data found for customer")
    return data

@router.get("/{customer_id}/range", response_model=list[schemas.ConsumptionProduction])
def get_consumption_data(customer_id: int, start: datetime, end: datetime, db: Session = Depends(get_db)):
    data = db.query(ConsumptionProduction).filter(
        ConsumptionProduction.customer_id == customer_id,
        ConsumptionProduction.timestamp >= start,
        ConsumptionProduction.timestamp <= end
    ).all()

    if not data: 
        raise HTTPException(status_code=404, detail="No data found for customer")
    
    return data
