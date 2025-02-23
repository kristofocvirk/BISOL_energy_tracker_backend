# BISOL_energy_tracker_backend

This application provides an API to interact with energy consumption and production data. It allows users to access and manage customer information, production/consumption data, and the SIPX euro price over time. It is built using **FastAPI**, **PostgreSQL**, and **Redis**.

## Features
- CRUD operations for customers.
- Access to hourly production/consumption data per customer.
- Retrieve hourly SIPX price data.
- Supports rate limiting.
- Caching enabled for certain operations.

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

### Adding data to the database
  To add the data entires present in the `data.csv` file use the following command.
  ```bash
  python -m app.add_customers.py 
  ```

### Running the App
To run the FastAPI app locally:

```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000` in your browser to access the API.

### Client test apps
Two client test apps are available in this repository: `heatmap.py` and `scatter_plot.py`.

`heatmap.py` fetches and calculates the average energy consumption for each day, then creates
a heatmap of average energy consumption for each day.

![alt text](images/heatmap.png)

`scatter_plot` fetches consumption/production data and SIPX price data and then plots a scatter plot of 
consumption/production against SIPX price. Consumption is marked red and production is marked green. 

![alt text](images/scatter_plot.png)