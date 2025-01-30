from fastapi import FastAPI
from routers import consumption_production, customers
from database import engine, Base

app = FastAPI()

# Initialize database
Base.metadata.create_all(bind=engine)

app.include_router(customers.router)
app.include_router(consumption_production.router)
