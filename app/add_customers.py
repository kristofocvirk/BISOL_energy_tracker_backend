import os
import pandas as pd
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from collections import defaultdict
import asyncio
from datetime import datetime
from app.models import Customer

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Create async database engine
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Create sessionmaker for async sessions
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Load CSV (adjust path if necessary based on Docker file location)
df = pd.read_csv("data.csv", sep=",")  # Ensure the file is available inside Docker

# Function to truncate all tables (async version)
async def truncate_tables(engine):
  async with engine.begin() as conn:
    await conn.execute(text("TRUNCATE TABLE consumption_production RESTART IDENTITY CASCADE;"))
    await conn.execute(text("TRUNCATE TABLE sipx_prices RESTART IDENTITY CASCADE;"))
    await conn.execute(text("TRUNCATE TABLE customers RESTART IDENTITY CASCADE;"))

# Async function to insert SIPX prices
async def insert_sipx_prices():
  df_renamed = df.rename(columns={
    "timestamp_utc": "timestamp",  # Change 'timestamp_utc' to 'timestamp'
    "SIPX_EUR_kWh": "price_EUR_kWh"  # Change 'SIPX_EUR_kWh' to 'price_EUR_kWh'
  })
  sipx_df = df_renamed[["timestamp", "price_EUR_kWh"]]
  async with async_session() as session:
    async with session.begin():
      for _, row in sipx_df.iterrows():
        timestamp = datetime.fromisoformat(row["timestamp"])
        await session.execute(
          text("""
            INSERT INTO sipx_prices ("timestamp", "price_EUR_kWh")
            VALUES (:timestamp, :price_EUR_kWh)
          """),
          {"timestamp": timestamp, "price_EUR_kWh": row["price_EUR_kWh"]}
        )
    await session.commit()  # Ensure commit after all insertions

# Async function to insert customer data
async def insert_customers():
  customer_roles = {}
  for col in df.columns:
    if col.startswith("customer"):
      parts = col.split("_")
      customer_name, data_type = parts[0], parts[1]

      if customer_name not in customer_roles:
        customer_roles[customer_name] = {"is_consumer": False, "is_producer": False}

      if data_type == "cons":
        customer_roles[customer_name]["is_consumer"] = True
      elif data_type == "prod":
        customer_roles[customer_name]["is_producer"] = True

  async with async_session() as session:
    async with session.begin():
      for customer, roles in customer_roles.items():
        await session.execute(
          text("""
            INSERT INTO customers (name, is_consumer, is_producer)
            VALUES (:name, :is_consumer, :is_producer)
            ON CONFLICT (name) DO UPDATE 
            SET is_consumer = EXCLUDED.is_consumer, 
                is_producer = EXCLUDED.is_producer;
          """),
          {"name": customer, "is_consumer": roles["is_consumer"], "is_producer": roles["is_producer"]}
        )

# Async function to get customer ids
async def get_customer_ids():
  async with async_session() as session:
    result = await session.execute(select(Customer.id, Customer.name))
    # Unpack the tuple and create a dictionary
    return {row.name: row.id for row in result.all()}

# Async function to insert production/consumption data
async def insert_prod_cons_data():
  customer_map = await get_customer_ids()

  combined_data = defaultdict(lambda: {"consumption_kWh": None, "production_kWh": None})

  for _, row in df.iterrows():
    for col in df.columns:
      if col.startswith("customer"):
        parts = col.split("_")
        customer_name, data_type = parts[0], parts[1]

        customer_id = customer_map.get(customer_name)
        if not customer_id:
          continue
        timestamp = datetime.fromisoformat(row["timestamp_utc"])
        key = (timestamp, customer_id)

        if data_type == "cons":
          combined_data[key]["consumption_kWh"] = row[col]
        elif data_type == "prod":
          combined_data[key]["production_kWh"] = row[col]

  prod_cons_data = [
    {
      "timestamp": key[0],
      "customer_id": key[1],
      "consumption_kWh": values["consumption_kWh"],
      "production_kWh": values["production_kWh"],
    }
    for key, values in combined_data.items()
  ]

  async with async_session() as session:
    async with session.begin():
      for data in prod_cons_data:
        await session.execute(
          text("""
              INSERT INTO consumption_production ("timestamp", "customer_id", "consumption_kWh", "production_kWh")
              VALUES (:timestamp, :customer_id, :consumption_kWh, :production_kWh)
          """),
          data
          )

# Main async function to execute all tasks
async def main():
  await truncate_tables(engine)
  await insert_sipx_prices()
  await insert_customers()
  await insert_prod_cons_data()

# Run the main function
asyncio.run(main())
