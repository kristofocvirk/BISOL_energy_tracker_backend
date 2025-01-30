from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Customer schema
class CustomerBase(BaseModel):
  name: str
  is_consumer : bool
  is_producer: bool

class CustomerCreate(CustomerBase):
  pass

class CustomerUpdate(CustomerBase):
  name : Optional[str] = None
  is_consumer : Optional[bool] = None
  is_producer : Optional[bool] = None

class Customer(CustomerBase):
  id: int
  deleted_at: Optional[datetime] = None

  class Config:
    from_attributes = True

# Consumption production schema
class ConsumptionProductionBase(BaseModel):
  timestamp: datetime
  consumption_kWh: Optional[float]
  production_kWh: Optional[float]

class ConsumptionProductionCreate(ConsumptionProductionBase):
  customer_id: int

class ConsumptionProductionUpdate(ConsumptionProductionBase):
  timestamp: Optional[datetime] = None
  consumption_kWh: Optional[float] = None
  production_kWh: Optional[float] = None

class ConsumptionProduction(ConsumptionProductionBase):
  id: int
  deleted_at: Optional[datetime] = None

  class Config:
    from_attributes = True

# Cost revenue schema 
class CostRevenueSummary(BaseModel):
  total_cost: float
  total_revenue: float  

# SIPX prices schema
class SIPXPriceBase(BaseModel):
  timestamp: datetime
  price_EUR_kWh: float

class SIPXPriceUpdate(SIPXPriceBase):
  timestamp: Optional[datetime] = None 
  price_EUR_kWh: Optional[float] = None

class SIPXPriceCreate(SIPXPriceBase):
  pass

class SIPXPrice(SIPXPriceBase):
  id: int

  class Config:
    from_attributes = True
