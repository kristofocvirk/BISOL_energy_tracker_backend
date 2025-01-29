from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CustomerBase(BaseModel):
    name: str
    role: str

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    id: int
    class Config:
        orm_mode = True

class ConsumptionProductionBase(BaseModel):
    timestamp: datetime
    consumption_kWh: Optional[float]
    production_kWh: Optional[float]

class ConsumptionProductionCreate(ConsumptionProductionBase):
    customer_id: int

class ConsumptionProduction(ConsumptionProductionBase):
    id: int

    class Config:
        orm_mode = True

class SIPXPriceBase(BaseModel):
    timestamp: datetime
    price_EUR_kWh: float

class SIPXPriceCreate(SIPXPriceBase):
    pass

class SIPXPrice(SIPXPriceBase):
    id: int

    class Config:
        orm_mode = True
