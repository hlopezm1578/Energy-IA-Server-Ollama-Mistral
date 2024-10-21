from pydantic import BaseModel
from datetime import datetime
from typing import Optional
   
class Estado(BaseModel):
    id: int
    nombre: str
    class Config:
        from_attributes = True

class AsistenteBase(BaseModel):
    nombre: str
    departamento: str
    chunks: int
    overlap: int

class AsistenteCreate(AsistenteBase):
    createdAt: datetime = datetime.now()
    createdBy: str = "Admin"
    version: int = 1
    active: bool = True
    estado_id: int = 1

class AsistenteUpdate(AsistenteBase):
    id:int
    updatedAt: datetime = datetime.now()
    updatedBy: str = 'Admin'
    version: Optional[int] = None
    active: Optional[bool] = None
    estado_id: int

class Asistente(AsistenteBase):
    id: int
    createdAt: datetime
    updatedAt: Optional[datetime]
    createdBy: str
    updatedBy: Optional[str]
    version: int
    active: bool
    estado: Estado 

    class Config:
        from_attribute = True
class TrainingRequest(BaseModel):
    asistente_id: int
    departamento: str
    chunks: int
    overlap: int



