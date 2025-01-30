from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, database

router = APIRouter(
    prefix="/consumption-production",
    tags=["Consumption production"]
)

# stranki doda časovno vrsto za stranko
@router.post("/", response_model=schemas.ConsumptionProduction)
def create_time_series(data: schemas.ConsumptionProductionCreate, db: Session = Depends(database.get_db)):
    # Ensure customer exists before inserting contuption-production data
    customer = db.query(models.Customer).filter(models.Customer.id == data.customer_id).first()
    if not customer:
        raise HTTPException(status_code=400, detail="Customer does not exist")

    # Ensure that the customer doesn't already have consumption-production data
    # at given timestamp
    consumption_production_data = (
        db.query(models.ConsumptionProduction)
        .filter(models.ConsumptionProduction.customer_id == data.customer_id)
        .filter(models.ConsumptionProduction.timestamp == data.timestamp)
        .first())

    if consumption_production_data:
        raise HTTPException(status_code=409, detail="Data already exists")

    time_series_entry = models.ConsumptionProduction(**data.model_dump())
    db.add(time_series_entry)
    db.commit()
    db.refresh(time_series_entry)
    return time_series_entry

@router.get("/{customer_id}", response_model=list[schemas.ConsumptionProduction])
def get_time_series(customer_id: int, db: Session = Depends(database.get_db)):
    data = db.query(models.ConsumptionProduction).filter(models.ConsumptionProduction.customer_id == customer_id).all()
    if not data:
        raise HTTPException(status_code=404, detail="No data found for customer")
    return data