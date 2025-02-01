# BISOL_energy_tracker_backend

This application provides an API to interact with energy consumption and production data. It allows users to access and manage customer information, production/consumption data, and the SIPX euro price over time. It is built using **FastAPI**, **PostgreSQL**, and **Redis**.

## Features
- CRUD operations for customers (consumers, producers, or both).
- Access to hourly production/consumption data per customer.
- Retrieve hourly SIPX price data.
- Supports rate limiting.
- Caching with redis enabled for certain operations.

## Technologies
- **FastAPI**: Python web framework for building APIs.
- **PostgreSQL**: Relational database for storing customer and time series data.
- **Redis**: Caching for improved performance.
- **SQLAlchemy**: ORM for database interactions.

## Setup

### Prerequisites
- Python 3.9+
- PostgreSQL database
- Docker (optional, for containerized setup)

### Install Dependencies

1. Clone the repository:

   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. Install the dependencies using your preferred method. If you’re using Docker, it’s recommended to build and run the app with Docker Compose.

   **Without Docker**:
   - Install Python dependencies:

     ```bash
     pip install -r requirements.txt
     ```

   **With Docker Compose** (recommended for ease of setup):
   - Build and start the app:

     ```bash
     docker-compose up --build
     ```

### Database Configuration
1. Create a PostgreSQL database and configure the connection details.
2. Update the connection string in `app/main.py`:

   ```python
   DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"
   ```

3. The database should be initialized automatically upon first start, but if you encounter any issues, run the migrations manually.

### Running the App
To run the FastAPI app locally:

```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000` in your browser to access the API.