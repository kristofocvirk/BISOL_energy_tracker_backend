from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "consumer", "producer", "both"
    data = relationship("ConsumptionProduction", back_populates="customer")

class ConsumptionProduction(Base):
    __tablename__ = "consumption_production"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    timestamp = Column(DateTime, nullable=False)
    consumption_kWh = Column(Float, nullable=True)
    production_kWh = Column(Float, nullable=True)
    customer = relationship("Customer", back_populates="data")

class SIPXPrice(Base):
    __tablename__ = "sipx_prices"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False)
    price_EUR_kWh = Column(Float, nullable=False)