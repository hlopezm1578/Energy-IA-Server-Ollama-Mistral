from models import Asistente
from sqlalchemy.orm import Session
from schemas import AsistenteCreate,AsistenteUpdate
from datetime import datetime

def create_asistente(db: Session, data: AsistenteCreate):
    asistente_instance = Asistente(**data.model_dump())
    db.add(asistente_instance)
    db.commit()
    db.refresh(asistente_instance)
    return asistente_instance

def get_asistente(db: Session):
    return db.query(Asistente).filter(Asistente.active==True).order_by(Asistente.id).all()

def get_asistente_by_id(db: Session, asistente_id: int):
    return db.query(Asistente).filter(Asistente.id == asistente_id).first()

def update_asistente(db: Session, asistente_id: int, data: AsistenteUpdate):
    asistente = db.query(Asistente).filter(Asistente.id == asistente_id).first()
    data.version = asistente.version + 1
    if asistente:
        for key, value in data.model_dump().items():
            setattr(asistente, key, value)
    db.commit()
    db.refresh(asistente)
    return asistente

def delete_asistente(db: Session, asistente_id: int):
    asistente = db.query(Asistente).filter(Asistente.id == asistente_id).first()
    if asistente:
        db.delete(asistente)
        db.commit()
        return asistente
    return None

def soft_delete_asistente(db: Session, asistente_id: int):
    asistente = db.query(Asistente).filter(Asistente.id == asistente_id).first()
    if asistente:
        asistente.active = False
        db.commit()
        db.refresh(asistente)
        return asistente
    return None

def change_status_asistente(db: Session, asistente_id: int, estado_id: int):
    asistente = db.query(Asistente).filter(Asistente.id == asistente_id).first()
    if asistente:
        asistente.estado_id = estado_id
    db.commit()
    db.refresh(asistente)
    return asistente
