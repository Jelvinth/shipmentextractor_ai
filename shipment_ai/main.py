from fastapi import FastAPI, Depends, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date
import tempfile
import os

import models
import schemas
import services
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Shipment Extractor API")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

from typing import List

@app.post("/api/upload/", response_model=List[schemas.ShipmentResponse])
async def upload_shipment_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Save to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name

    try:
        # Extract text from PDF
        pdf_text = services.extract_text_from_pdf(temp_file_path)
        if not pdf_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")

        # Parse text with GenAI
        parsed_data = services.parse_shipment_data_from_text(pdf_text)
        if not parsed_data:
             raise HTTPException(status_code=500, detail="Failed to parse data with AI")
             
        # Extract container list
        container_numbers = parsed_data.get("container_numbers", [])
        if not container_numbers and parsed_data.get("container_number"):
            container_numbers = [parsed_data.get("container_number")]
            
        responses = []
        for c_num in container_numbers:
            if not c_num: continue
            
            shipment_data = parsed_data.copy()
            shipment_data["container_number"] = c_num
            shipment_data.pop("container_numbers", None)
            
            shipment_create = schemas.ShipmentCreate(**shipment_data)
            
            # Check if container already exists
            existing = services.get_shipment_by_container(db, shipment_create.container_number)
            if existing:
                db_shipment = existing
            else:
                db_shipment = services.create_shipment(db, shipment_create)
            
            # Calculate status
            response = schemas.ShipmentResponse.model_validate(db_shipment)
            response.status = response.get_status()
            responses.append(response)
        
        return responses

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.post("/api/summarize/", response_model=schemas.SummaryResponse)
async def summarize_shipment_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name

    try:
        pdf_text = services.extract_text_from_pdf(temp_file_path)
        if not pdf_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")

        summary = services.summarize_shipment_document(pdf_text)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/api/shipment/{container_number}", response_model=schemas.ShipmentResponse)
def read_shipment(container_number: str, db: Session = Depends(get_db)):
    db_shipment = services.get_shipment_by_container(db, container_number=container_number)
    if db_shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
        
    response = schemas.ShipmentResponse.model_validate(db_shipment)
    response.status = response.get_status()
    
    return response

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
