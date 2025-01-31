from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from app.database import Base  # Adjust this import to point to your actual Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# Target metadata for 'autogenerate' support
target_metadata = Base.metadata

# URL for the async engine
def get_url():
    return config.get_main_option("sqlalchemy.url")

# Create the async engine
async def run_migrations_online():
    # Ensure we use async engine
    connectable = create_async_engine(get_url(), poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

async def do_run_migrations(connection):
    # Run migrations inside a transaction
    with context.begin_transaction():
        context.run_migrations()

# Run migrations online with async engine
async def main():
    await run_migrations_online()

# Start the migration process
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())  # Ensure the async main function is run