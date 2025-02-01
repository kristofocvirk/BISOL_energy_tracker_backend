import asyncio
import httpx
import matplotlib.pyplot as plt
import pandas as pd

BASE_URL = "http://localhost:8000"

async def fetch_customers(client):
  """Fetch customer data to determine if they are producers, consumers, or both."""
  response = await client.get(f"{BASE_URL}/customers/")
  if response.status_code == 200:
    return response.json()
  else:
    print("Failed to fetch customer data")
    return []

async def fetch_user_data(client, user_id):
  """Fetch consumption and production data for a given user."""
  response = await client.get(f"{BASE_URL}/consumption-production/{user_id}")
  if response.status_code == 200:
    df = pd.DataFrame(response.json())
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["user_id"] = user_id
    return df
  else:
    print(f"Failed to fetch data for user {user_id}")
    return pd.DataFrame()

async def get_sipx_prices():
  """Fetch SIPX price data."""
  async with httpx.AsyncClient() as client:
    response = await client.get(f"{BASE_URL}/sipx-prices/")
    if response.status_code == 200:
      df = pd.DataFrame(response.json())
      df["timestamp"] = pd.to_datetime(df["timestamp"])
      return df
    else:
      print("Failed to fetch SIPX prices")
      return pd.DataFrame()

async def main():
  async with httpx.AsyncClient() as client:
    # Fetch customers
    customers = await fetch_customers(client)
    user_ids = [c["id"] for c in customers]  # Get all customer IDs

    # Fetch SIPX prices
    sipx_data = await get_sipx_prices()

    # Fetch energy data for each user
    tasks = [fetch_user_data(client, user_id) for user_id in user_ids]
    user_data_list = await asyncio.gather(*tasks)

    # Combine all users' data into one DataFrame
    energy_data = pd.concat(user_data_list, ignore_index=True)

    # Merge energy data with SIPX prices
    merged_data = pd.merge(energy_data, sipx_data, on="timestamp")

    # Identify consumer and producer data
    consumers = {c["id"] for c in customers if c["is_consumer"]}
    producers = {c["id"] for c in customers if c["is_producer"]}

    # Scatter plot of SIPX price vs. Energy Consumption/Production
    plt.figure(figsize=(12, 6))
    
    # Plot consumers
    consumer_data = merged_data[merged_data["user_id"].isin(consumers)]
    plt.scatter(consumer_data["price_EUR_kWh"], consumer_data["consumption_kWh"], 
                alpha=0.5, color="red", label="Consumption")
    
    # Plot producers
    producer_data = merged_data[merged_data["user_id"].isin(producers)]
    plt.scatter(producer_data["price_EUR_kWh"], producer_data["production_kWh"], 
                alpha=0.5, color="green", label="Production")

    plt.xlabel("SIPX Price (€)")
    plt.ylabel("Energy (kWh)")
    plt.title("SIPX Price vs. Energy Consumption/Production")
    plt.legend()
    plt.grid()
    plt.show()

asyncio.run(main())