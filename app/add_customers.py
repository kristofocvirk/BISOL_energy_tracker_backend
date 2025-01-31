import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Create database engine
engine = create_engine(DATABASE_URL)

# Load CSV
df = pd.read_csv("data.csv", sep=",")  # Adjust separator if needed

# Function to truncate all tables
def truncate_tables(engine):
  with engine.begin() as conn:
    conn.execute(text("TRUNCATE TABLE consumption_production RESTART IDENTITY CASCADE;"))
    conn.execute(text("TRUNCATE TABLE sipx_prices RESTART IDENTITY CASCADE;"))
    conn.execute(text("TRUNCATE TABLE customers RESTART IDENTITY CASCADE;"))

# Truncate tables before inserting new data
truncate_tables(engine)

# Insert SIPX prices
df = df.rename(columns={
  "timestamp_utc": "timestamp",  # Change 'timestamp_utc' to 'timestamp'
  "SIPX_EUR_kWh": "price_EUR_kWh"  # Change 'SIPX_EUR_kWh' to 'price_EUR_kWh'
})

sipx_df = df[["timestamp", "price_EUR_kWh"]]
sipx_df.to_sql("sipx_prices", engine, if_exists="append", index=False)

# Extract unique customer names
customers = {col.split("_")[0] for col in df.columns if col.startswith("customers")}

# Extract unique customer names and determine roles
customer_roles = {}
for col in df.columns:
  if col.startswith("customer"):
    parts = col.split("_")
    customer_name, data_type = parts[0], parts[1]  # e.g., "customer00", "cons"

    if customer_name not in customer_roles:
      customer_roles[customer_name] = {"is_consumer": False, "is_producer": False}

    if data_type == "cons":
      customer_roles[customer_name]["is_consumer"] = True
    elif data_type == "prod":
      customer_roles[customer_name]["is_producer"] = True

# Insert customers with is_consumer and is_producer flags
with engine.begin() as conn:
  for customer, roles in customer_roles.items():
    conn.execute(
      text("""
        INSERT INTO customers (name, is_consumer, is_producer)
        VALUES (:name, :is_consumer, :is_producer)
        ON CONFLICT (name) DO UPDATE 
        SET is_consumer = EXCLUDED.is_consumer, 
            is_producer = EXCLUDED.is_producer;
      """),
      {"name": customer, "is_consumer": roles["is_consumer"], "is_producer": roles["is_producer"]}
    )
  
  # Get customer IDs
  customer_map = {
    row["name"]: row["id"]
    for row in conn.execute(text("SELECT id, name FROM customers")).mappings()
  }

# Process production/consumption data
# Assuming customer_map is a dictionary of customer_name -> customer_id

consumer_data = []
for col in df.columns:
  if col.startswith("customer"):  # Check for customer columns
    parts = col.split("_")
    customer_name, data_type = parts[0], parts[1]
      
    customer_id = customer_map.get(customer_name)
    if not customer_id:
      continue

    # Set flags for is_consumer and is_producer
    is_consumer = (data_type == "cons")
    is_producer = (data_type == "prod")
      
    # Prepare data for insertion into consumer table
    consumer_data.append({
      "customer_id": customer_id,
      "name": customer_name,
      "is_consumer": is_consumer,
      "is_producer": is_producer
    })

# Convert to DataFrame for batch insert
df_consumers = pd.DataFrame(consumer_data)

# Assuming you have an SQLAlchemy engine set up
df_consumers.to_sql("consumers", engine, if_exists="append", index=False)

# Initialize a dictionary to store combined data
combined_data = defaultdict(lambda: {"consumption_kWh": None, "production_kWh": None})

# Iterate through each row in the dataframe
for _, row in df.iterrows():
  # Iterate over customer columns (those starting with "customer")
  for col in df.columns:
    if col.startswith("customer"):  # Identifies customer-related columns
      parts = col.split("_")
      customer_name, data_type = parts[0], parts[1]

      # Get customer_id from the customer map
      customer_id = customer_map.get(customer_name)
      if not customer_id:
        continue  # Skip if customer_id not found

      # Create a unique key for the timestamp and customer_id
      key = (row["timestamp"], customer_id)

      # Update consumption or production value based on the data_type
      if data_type == "cons":
        combined_data[key]["consumption_kWh"] = row[col]
      elif data_type == "prod":
        combined_data[key]["production_kWh"] = row[col]

# Convert the combined data into a list of dictionaries
prod_cons_data = [
  {
    "timestamp": key[0],
    "customer_id": key[1],
    "consumption_kWh": values["consumption_kWh"],
    "production_kWh": values["production_kWh"],
  }
  for key, values in combined_data.items()
]

# Convert the list of dictionaries to a DataFrame
df_prod_cons = pd.DataFrame(prod_cons_data)

# Insert data into the consumption_production table
df_prod_cons.to_sql("consumption_production", engine, if_exists="append", index=False)