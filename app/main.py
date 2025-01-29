from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

# Initialize database
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Models
class CustomerBase(BaseModel):
    name: str
    is_producer: bool

class TimeSeriesBase(BaseModel):
    customer_id: int
    timestamp: datetime
    consumption_kWh: float
    production_kWh: float
    price_eur_kWh: float

# CRUD Endpoints

@app.post("/customers/")
def create_customer(customer: CustomerBase, db: Session = Depends(get_db)):
    db_customer = models.Customer(name=customer.name, is_producer=customer.is_producer)
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@app.get("/customers/{customer_id}")
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.post("/time-series/")
def create_time_series(data: TimeSeriesBase, db: Session = Depends(get_db)):
    time_series_entry = models.TimeSeries(**data.dict())
    db.add(time_series_entry)
    db.commit()
    db.refresh(time_series_entry)
    return time_series_entry

@app.get("/time-series/{customer_id}")
def get_time_series(customer_id: int, db: Session = Depends(get_db)):
    data = db.query(models.TimeSeries).filter(models.TimeSeries.customer_id == customer_id).all()
    if not data:
        raise HTTPException(status_code=404, detail="No data found for customer")
    return data
