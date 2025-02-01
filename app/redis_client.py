import redis
from fastapi import Depends

# Define settings to load from .env
redis_host: str = "localhost"
redis_port: int = 6379
redis_db: int = 0


# Initialize the Redis client
def get_redis():
  return redis.Redis(host=redis_host, port=redis_port, db=redis_db)

# Dependency
def get_redis_client(redis: redis.Redis = Depends(get_redis)):
  return redis