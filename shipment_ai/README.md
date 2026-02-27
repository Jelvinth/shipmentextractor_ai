# Shipment Extractor API

A FastAPI application that processes shipment PDF documents. It extracts key information from uploaded PDFs such as consignee, shipper, container numbers, and ETA, using AI-powered text parsing, and stores them in a local SQLite database.

## Features

- **Upload PDF:** Extracts shipment details and multiple container numbers from a single file.
- **Track Container:** Retrieve shipment data by container number.
- **ETA Status:** Automatically checks if a shipment is "Delayed" based on its ETA compared to the current date.

## Requirements

- Python 3+
- See `requirements.txt` for dependencies (FastAPI, SQLAlchemy, uvicorn, etc.)

## Setup and Running

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the server:
   ```bash
   uvicorn main:app --reload
   ```


## Database

By default, an SQLite database (`shipments.db`) will be automatically created in the root directory upon server startup.
