from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Customer(Base):
  __tablename__ = "customers"

  id = Column(Integer, primary_key=True, index=True)
  name = Column(String, unique=True, nullable=False)
  is_producer = Column(Boolean, nullable=False)
  is_consumer = Column(Boolean, nullable=False)
  deleted_at = Column(DateTime(timezone=True), nullable=True) # soft delete column

  data = relationship("ConsumptionProduction", back_populates="customer")

  def to_dict(self):
    return {
    "id": self.id,
    "name": self.name,
    "is_producer": self.is_producer,
    "is_consumer": self.is_consumer,
    "deleted_at": self.deleted_at
    }

class ConsumptionProduction(Base):
  __tablename__ = "consumption_production"

  id = Column(Integer, primary_key=True, index=True)
  customer_id = Column(Integer, ForeignKey("customers.id"))
  timestamp = Column(DateTime(timezone=True), nullable=False)
  consumption_kWh = Column(Float, nullable=True)
  production_kWh = Column(Float, nullable=True)
  deleted_at = Column(DateTime, nullable=True)  # Soft delete column

  customer = relationship("Customer", back_populates="data")

  def to_dict(self):
    return {
      "id": self.id,
      "customer_id": self.customer_id, 
      "timestamp": self.timestamp.isoformat(),  
      "consumption_kWh": self.consumption_kWh,
      "production_kWh": self.production_kWh, 
      "deleted_a": self.deleted_at
    }

class SIPXPrice(Base):
  __tablename__ = "sipx_prices"

  id = Column(Integer, primary_key=True, index=True)
  timestamp = Column(DateTime(timezone=True), nullable=False)
  price_EUR_kWh = Column(Float, nullable=False)

  def to_dict(self):
    return {
      "id": self.id,
      "timestamp": self.timestamp.isoformat(),  
      "price_EUR_kWh": self.price_EUR_kWh
    }