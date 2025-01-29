from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas import Customer, CustomerCreate
from crud import get_customers, create_customer
from database import get_db

router = APIRouter()

@router.get("/", response_model=list[Customer])
def read_customers(db: Session = Depends(get_db)):
    return get_customers(db)

@router.post("/", response_model=Customer)
def add_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    return create_customer(db, customer)
