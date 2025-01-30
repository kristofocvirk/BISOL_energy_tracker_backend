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

# naredi novo stranko
@router.post("/")
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
  db_customer = Customer(name=customer.name, is_producer=customer.is_producer, is_consumer=customer.is_consumer)
  db.add(db_customer)
  db.commit()
  db.refresh(db_customer)
  return db_customer

# pridobi podatke o stranki
@router.get("/{customer_id}")
def get_customer(customer_id: int, db: Session = Depends(get_db)):
  customer = db.query(Customer).filter(Customer.id == customer_id, Customer.deleted_at == None).first()
  if not customer:
    raise HTTPException(status_code=404, detail="Customer not found")
  return customer

# pridobi vse stranke
@router.get("/")
def get_customers(db: Session = Depends(get_db)):
    return db.query(Customer).filter(Customer.deleted_at == None).all()

# stranko in njeno časovno vrsto označi za izbrisano
@router.delete("/customers/{customer_id}")
def soft_delete_customer(customer_id: int, db: Session = Depends(get_db)):
  customer = db.query(Customer).filter(Customer.id == customer_id, Customer.deleted_at == None).first()
  if not customer:
      raise HTTPException(status_code=404, detail="Customer not found or already deleted")

  # stranko označi za izbrisano
  customer.deleted_at = datetime.now(timezone.utc)
  db.query(ConsumptionProduction).filter(ConsumptionProduction.customer_id == customer_id).update(
      {"deleted_at": datetime.now(timezone.utc)}
  )
  
  db.commit()
  return {"message": f"Customer {customer_id} and associated data marked as deleted"}

# obnovi stranko in njeno časovno vrsto
@router.put("/customers/{customer_id}/restore", response_model=schemas.Customer)
def restore_customer(customer_id: int, db: Session = Depends(get_db)):
  customer = db.query(Customer).filter(Customer.id == customer_id).first()
  
  if not customer:
      raise HTTPException(status_code=404, detail="Customer not found")
  
  if customer.deleted_at is None:
      raise HTTPException(status_code=400, detail="Customer is already active")
  
  customer.deleted_at = None  #obnovi stranko
  db.commit()
  db.refresh(customer)

  return customer

# posodobi stranko
@router.patch("/{customer_id}", response_model=schemas.CustomerUpdate)
def update_customer(customer_id: int, update_data: schemas.CustomerUpdate, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if update_data.name is not None:
        customer.name = update_data.name

    if update_data.is_consumer is not None:
        customer.is_consumer = update_data.is_consumer

    if update_data.is_producer is not None:
        customer.is_producer = update_data.is_producer

    db.commit()
    db.refresh(customer)
    return customer