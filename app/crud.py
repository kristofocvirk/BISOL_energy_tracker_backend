from sqlalchemy.orm import Session
from models import Customer, ConsumptionProduction, SIPXPrice
from schemas import CustomerCreate, ConsumptionProductionCreate, SIPXPriceCreate

def get_customers(db: Session):
    return db.query(Customer).all()

def create_customer(db: Session, customer: CustomerCreate):
    db_customer = Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def get_consumption_data(db: Session, customer_id: int, start: datetime, end: datetime):
    return db.query(ConsumptionProduction).filter(
        ConsumptionProduction.customer_id == customer_id,
        ConsumptionProduction.timestamp >= start,
        ConsumptionProduction.timestamp <= end
    ).all()

def calculate_cost_revenue(db: Session, customer_id: int, start: datetime, end: datetime):
    data = get_consumption_data(db, customer_id, start, end)
    prices = db.query(SIPXPrice).filter(
        SIPXPrice.timestamp.between(start, end)
    ).all()
    price_map = {price.timestamp: price.price_EUR_kWh for price in prices}

    total_cost = sum(d.consumption_kWh * price_map[d.timestamp] for d in data if d.consumption_kWh)
    total_revenue = sum(d.production_kWh * price_map[d.timestamp] for d in data if d.production_kWh)

    return {"total_cost": total_cost, "total_revenue": total_revenue}
