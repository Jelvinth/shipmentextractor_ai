from sqlalchemy import Column, Integer, String, Date
from database import Base

class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    container_number = Column(String, unique=True, index=True)
    consignee = Column(String)
    shipper = Column(String)
    eta = Column(Date)
    port_of_loading = Column(String)
    port_of_discharge = Column(String)
