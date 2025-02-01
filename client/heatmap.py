import asyncio
import httpx
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

BASE_URL = "http://localhost:8000"

async def fetch_user_data(client, user_id):
  """Fetch consumption data for a given user."""
  response = await client.get(f"{BASE_URL}/consumption-production/{user_id}")
  if response.status_code == 200:
    df = pd.DataFrame(response.json())
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["user_id"] = user_id
    return df
  else:
    print(f"Failed to fetch data for user {user_id}")
    return pd.DataFrame()

async def fetch_customers(client):
  """Fetch customer data to identify consumers."""
  response = await client.get(f"{BASE_URL}/customers/")
  if response.status_code == 200:
    return response.json()
  else:
    print("Failed to fetch customer data")
    return []

async def main():
  async with httpx.AsyncClient() as client:
    # Fetch customers and identify consumers
    customers = await fetch_customers(client)
    consumer_ids = [c["id"] for c in customers if c["is_consumer"]]

    # Fetch consumption data for consumers
    tasks = [fetch_user_data(client, user_id) for user_id in consumer_ids]
    user_data_list = await asyncio.gather(*tasks)

    # Combine all users' data into one DataFrame
    energy_data = pd.concat(user_data_list, ignore_index=True)
    if energy_data.empty:
      print("Error: No energy data available.")
      return

    # Extract hour and day from timestamps
    energy_data["day"] = energy_data["timestamp"].dt.date
    energy_data["hour"] = energy_data["timestamp"].dt.hour

    # Aggregate average consumption per hour for each day
    heatmap_data = (
      energy_data.groupby(["day", "hour"])["consumption_kWh"]
      .mean()
      .unstack()
    )

    # Plot heatmap
    plt.figure(figsize=(12, 6))
    sns.heatmap(
      heatmap_data.T, cmap="coolwarm", linewidths=0.5, annot=False
    )
    plt.xlabel("Day")
    plt.ylabel("Hour of the Day")
    plt.title("Average Energy Consumption per Hour")
    plt.show()

asyncio.run(main())