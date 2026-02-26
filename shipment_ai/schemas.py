from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional

class ShipmentBase(BaseModel):
    container_number: Optional[str] = None
    consignee: Optional[str] = None
    shipper: Optional[str] = None
    eta: Optional[date] = None
    port_of_loading: Optional[str] = None
    port_of_discharge: Optional[str] = None

class ShipmentCreate(ShipmentBase):
    pass

class ShipmentResponse(ShipmentBase):
    id: int
    status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
    
    def get_status(self) -> str:
        if self.eta is None:
             return "Unknown"
        if self.eta < date.today():
             return "Delayed"
        return "On Time"

