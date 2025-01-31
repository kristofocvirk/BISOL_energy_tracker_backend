from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL)
# Create a session factory for AsyncSession
AsyncSessionLocal = sessionmaker(
  bind=engine,
  class_=AsyncSession,
  expire_on_commit=False,
)
Base = declarative_base()

async def get_db():
  db = AsyncSessionLocal()
  async with AsyncSessionLocal() as db:
    try:
      yield db
    finally:
      await db.close()