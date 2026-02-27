import pdfplumber
import os
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
import models
import schemas

# Pydantic schema for structured output from Gemini
class ExtractedShipmentData(BaseModel):
    consignee: Optional[str]
    shipper: Optional[str]
    container_numbers: list[str]
    eta: Optional[date]
    port_of_loading: Optional[str]
    port_of_discharge: Optional[str]

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def parse_shipment_data_from_text(text: str) -> dict:
    # Fetch the key dynamically from Render's environment
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set. Please check Render dashboard.")
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are an expert AI logistics parsing assistant.
    Extract the following information from the provided Bill of Lading (BL) or Invoice document text.
    
    Required fields:
    - consignee
    - shipper
    - container_numbers (extract all container numbers found as a list of strings)
    - eta (Estimated Time of Arrival) - Note that the ETA in the document might be formatted as 'DTD:DD/MM/YYYY' or similar formats (e.g., 'DTD:11/08/2025'). Please parse this correctly and output ONLY in YYYY-MM-DD format.
    - port_of_loading
    - port_of_discharge
    
    Document Text:
    {text}
    """
    
    try:
         result = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExtractedShipmentData,
                temperature=0.1,
            ),
        )
         # Result structured output comes nicely using pydantic from newer genai sdk
         json_result = result.text
         import json
         data = json.loads(json_result)
         return data
    except Exception as e:
         print(f"Error calling Gemini API: {e}")
         return {}

def summarize_shipment_document(text: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set. Please check Render dashboard.")
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Please provide a concise summary of the following shipment document. 
    Highlight the key details such as the parties involved, the main items being shipped, the origin and destination, and any important dates or special instructions.
    
    Document Text:
    {text}
    """
    
    try:
         result = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
         return result.text
    except Exception as e:
         print(f"Error calling Gemini API for summary: {e}")
         return "Failed to generate summary."


def create_shipment(db: Session, shipment: schemas.ShipmentCreate):
    db_shipment = models.Shipment(**shipment.model_dump())
    db.add(db_shipment)
    db.commit()
    db.refresh(db_shipment)
    return db_shipment

def get_shipment_by_container(db: Session, container_number: str):
    return db.query(models.Shipment).filter(models.Shipment.container_number == container_number).first()
