from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class Customer(Base):
  __tablename__ = "customers"

  id = Column(Integer, primary_key=True, index=True)
  name = Column(String, nullable=False)
  is_producer = Column(Boolean, nullable=False)
  is_consumer = Column(Boolean, nullable=False)
  deleted_at = Column(DateTime, nullable=True) # soft delete column

  data = relationship("ConsumptionProduction", back_populates="customer")

class ConsumptionProduction(Base):
  __tablename__ = "consumption_production"

  id = Column(Integer, primary_key=True, index=True)
  customer_id = Column(Integer, ForeignKey("customers.id"))
  timestamp = Column(DateTime, nullable=False)
  consumption_kWh = Column(Float, nullable=True)
  production_kWh = Column(Float, nullable=True)
  deleted_at = Column(DateTime, nullable=True)  # Soft delete column

  customer = relationship("Customer", back_populates="data")

class SIPXPrice(Base):
  __tablename__ = "sipx_prices"

  id = Column(Integer, primary_key=True, index=True)
  timestamp = Column(DateTime, nullable=False)
  price_EUR_kWh = Column(Float, nullable=False)