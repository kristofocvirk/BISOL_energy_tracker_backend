from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import schemas 
from datetime import datetime, timezone
from models import Customer, ConsumptionProduction

router = APIRouter(
  prefix="/customers",
  tags=["Customers"]
)

# create new customer 
@router.post("/")
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
  db_customer = Customer(name=customer.name, is_producer=customer.is_producer, is_consumer=customer.is_consumer)
  db.add(db_customer)
  db.commit()
  db.refresh(db_customer)
  return db_customer

# get information about a customer 
@router.get("/{customer_id}")
def get_customer(customer_id: int, db: Session = Depends(get_db)):
  customer = db.query(Customer).filter(Customer.id == customer_id, Customer.deleted_at == None).first()
  if not customer:
    raise HTTPException(status_code=404, detail="Customer not found")
  return customer

# get all customers
@router.get("/")
def get_customers(db: Session = Depends(get_db)):
  return db.query(Customer).filter(Customer.deleted_at == None).all()

# gets all customers with specified name 
# function can be expanded with unique identifiers like email
@router.get("/search/", response_model=list[schemas.Customer])
def search_customer(name: str, db: Session = Depends(get_db)):
    customers = db.query(Customer).filter(Customer.name.ilike(f"%{name}%")).all()
    
    if not customers:
        raise HTTPException(status_code=404, detail="No customers found")

    return customers

# marks a customer and their consumption-production data as deleted
@router.delete("/customers/{customer_id}")
def soft_delete_customer(customer_id: int, db: Session = Depends(get_db)):
  customer = db.query(Customer).filter(Customer.id == customer_id, Customer.deleted_at == None).first()
  if not customer:
    raise HTTPException(status_code=404, detail="Customer not found or already deleted")

  # marks the customer and their data as deleted
  customer.deleted_at = datetime.now(timezone.utc)
  db.query(ConsumptionProduction).filter(ConsumptionProduction.customer_id == customer_id).update(
    {"deleted_at": datetime.now(timezone.utc)}
  )
  
  db.commit()
  return {"message": f"Customer {customer_id} and associated data marked as deleted"}

# deletes a customer if they had no associated data
@router.delete("/{customer_id}", status_code=204)
def delete_customer_if_no_data(customer_id: int, db: Session = Depends(get_db)):
    # Check if the customer has any associated consumption or production data
    has_data = db.query(ConsumptionProduction).filter(
        (ConsumptionProduction.customer_id == customer_id)
    ).first()

    if has_data:
        raise HTTPException(status_code=400, detail="Customer has associated data and cannot be deleted")

    # If no data exists, proceed to delete the customer
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    db.delete(customer)
    db.commit()
    
    return {"detail": "Customer deleted successfully"}

# restores a customer and their data
@router.put("/customers/{customer_id}/restore", response_model=schemas.Customer)
def restore_customer(customer_id: int, db: Session = Depends(get_db)):
  customer = db.query(Customer).filter(Customer.id == customer_id).first()
  
  if not customer:
    raise HTTPException(status_code=404, detail="Customer not found")
  
  if customer.deleted_at is None:
    raise HTTPException(status_code=400, detail="Customer is already active")
  
  customer.deleted_at = None  
  db.commit()
  db.refresh(customer)

  return customer

# updates the customer's name, is_consumer or is_producer
@router.patch("/{customer_id}", response_model=schemas.CustomerUpdate)
def update_customer(customer_id: int, update_data: schemas.CustomerUpdate, db: Session = Depends(get_db)):
  customer = db.query(Customer).filter(Customer.id == customer_id).first()
  if not customer:
    raise HTTPException(status_code=404, detail="Customer not found")

  #updates the specified fields
  if update_data.name is not None:
    customer.name = update_data.name

  if update_data.is_consumer is not None:
    customer.is_consumer = update_data.is_consumer

  if update_data.is_producer is not None:
    customer.is_producer = update_data.is_producer

  db.commit()
  db.refresh(customer)
  return customer