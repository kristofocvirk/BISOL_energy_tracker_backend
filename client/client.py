import asyncio
import matplotlib.pyplot as plt
import pandas as pd
import httpx

BASE_URL = "http://localhost:8000"

async def simulate_client(client_id):
  async with httpx.AsyncClient() as client:
    response = await client.get(f"{BASE_URL}/customers/{client_id}")
    print(f"Client {client_id} received:", response.json())

async def get_sipx_prices():
  async with httpx.AsyncClient() as client:
    response = await client.get(f"{BASE_URL}/sipx-prices/")
    data = response.json()

    # Convert to DataFrame
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])  # Ensure timestamps are datetime
    df = df.sort_values("timestamp")  # Sort by time

    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(df["timestamp"], df["price_EUR_kWh"], label="SIPX Price", color="blue")
    plt.xlabel("Time")
    plt.ylabel("Price (€)")
    plt.title("SIPX Energy Prices Over Time")
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid()
    plt.show()

async def main():
  client_ids = range(1,15)
  tasks = [simulate_client(cid) for cid in client_ids]
  await asyncio.gather(*tasks)
  await get_sipx_prices()



asyncio.run(main())