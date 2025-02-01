from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db 
import schemas
from datetime import datetime, timezone
from models import Customer, ConsumptionProduction
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)

# create new customer 
@router.post("/")
@limiter.limit("20/minute")
async def create_customer(request: Request, customer: schemas.CustomerCreate, db: AsyncSession = Depends(get_db)):
  db_customer = Customer(name=customer.name, is_producer=customer.is_producer, is_consumer=customer.is_consumer)
  db.add(db_customer)
  await db.commit()  # Asynchronous commit
  await db.refresh(db_customer)  # Asynchronous refresh
  return db_customer

# get information about a customer 
@router.get("/{customer_id}")
@limiter.limit("20/minute")
async def get_customer(request: Request, customer_id: int, db: AsyncSession = Depends(get_db)):
  result = await db.execute(select(Customer).filter(Customer.id == customer_id, Customer.deleted_at == None))
  customer = result.scalars().first()  # async version of query
  if not customer:
    raise HTTPException(status_code=404, detail="Customer not found")
  return customer

# get all customers
@router.get("/")
@limiter.limit("20/minute")
async def get_customers(request: Request, db: AsyncSession = Depends(get_db)):
  result = await db.execute(select(Customer).filter(Customer.deleted_at == None))
  return result.scalars().all()  # async version of query

# gets all customers with specified name 
@router.get("/search/", response_model=list[schemas.Customer])
@limiter.limit("20/minute")
async def search_customer(request: Request, name: str, db: AsyncSession = Depends(get_db)):
  result = await db.execute(select(Customer).filter(Customer.name.ilike(f"%{name}%")))
  customers = result.scalars().all()
  
  if not customers:
    raise HTTPException(status_code=404, detail="No customers found")

  return customers

# marks a customer and their consumption-production data as deleted
@router.delete("/customers/{customer_id}")
@limiter.limit("20/minute")
async def soft_delete_customer(request: Request, customer_id: int, db: AsyncSession = Depends(get_db)):
  result = await db.execute(select(Customer).filter(Customer.id == customer_id, Customer.deleted_at == None))
  customer = result.scalars().first()
  if not customer:
    raise HTTPException(status_code=404, detail="Customer not found or already deleted")

  # marks the customer and their data as deleted
  customer.deleted_at = datetime.now(timezone.utc)
  await db.execute(
    select(ConsumptionProduction).filter(ConsumptionProduction.customer_id == customer_id).update(
      {"deleted_at": datetime.now(timezone.utc)}
    )
  )
  await db.commit()
  return {"message": f"Customer {customer_id} and associated data marked as deleted"}

# deletes a customer if they had no associated data
@router.delete("/{customer_id}", status_code=204)
@limiter.limit("20/minute")
async def delete_customer_if_no_data(request: Request, customer_id: int, db: AsyncSession = Depends(get_db)):
  result = await db.execute(select(ConsumptionProduction).filter(ConsumptionProduction.customer_id == customer_id))
  has_data = result.scalars().first()

  if has_data:
    raise HTTPException(status_code=400, detail="Customer has associated data and cannot be deleted")

  result = await db.execute(select(Customer).filter(Customer.id == customer_id))
  customer = result.scalars().first()

  if not customer:
    raise HTTPException(status_code=404, detail="Customer not found")

  await db.delete(customer)  # async delete
  await db.commit()  # async commit

  return {"detail": "Customer deleted successfully"}

# restores a customer and their data
@router.put("/customers/{customer_id}/restore", response_model=schemas.Customer)
@limiter.limit("20/minute")
async def restore_customer(request: Request, customer_id: int, db: AsyncSession = Depends(get_db)):
  result = await db.execute(select(Customer).filter(Customer.id == customer_id))
  customer = result.scalars().first()

  if not customer:
    raise HTTPException(status_code=404, detail="Customer not found")
  
  if customer.deleted_at is None:
    raise HTTPException(status_code=400, detail="Customer is already active")
  
  customer.deleted_at = None  
  await db.commit()  # async commit
  await db.refresh(customer)  # async refresh

  return customer

# updates the customer's name, is_consumer or is_producer
@router.patch("/{customer_id}", response_model=schemas.CustomerUpdate)
@limiter.limit("20/minute")
async def update_customer(request: Request, customer_id: int, update_data: schemas.CustomerUpdate, db: AsyncSession = Depends(get_db)):
  result = await db.execute(select(Customer).filter(Customer.id == customer_id))
  customer = result.scalars().first()
  if not customer:
    raise HTTPException(status_code=404, detail="Customer not found")

  # Update the specified fields
  if update_data.name is not None:
    customer.name = update_data.name

  if update_data.is_consumer is not None:
    customer.is_consumer = update_data.is_consumer

  if update_data.is_producer is not None:
    customer.is_producer = update_data.is_producer

  await db.commit()  # async commit
  await db.refresh(customer)  # async refresh
  return customer