import asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from routers import consumption_production, customers, sipx_prices
from database import Base, engine

app = FastAPI()

# Async function to initialize the database schema
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("startup")
async def startup():
    await init_db()

# Include routers
app.include_router(customers.router)
app.include_router(consumption_production.router)
app.include_router(sipx_prices.router)
