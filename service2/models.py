from db import Base
from sqlalchemy import Column, Integer, String, Float,DateTime,Boolean,ForeignKey
from sqlalchemy.orm import relationship

class BaseEntity(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    createdAt = Column(DateTime, nullable=False)
    updatedAt = Column(DateTime,nullable=True)
    createdBy = Column(String, nullable=False)
    updatedBy = Column(String,nullable=True)
    version = Column(Integer, nullable=False)
    active = Column(Boolean, nullable=False)

class Asistente(BaseEntity):
    __tablename__ = 'Asistentes'
    nombre = Column(String,nullable=False)
    departamento = Column(String,nullable=False)
    chunks = Column(Integer,nullable=False)
    overlap = Column(Integer,nullable=False)
    estado_id = Column(Integer,ForeignKey('Estados.id') ,nullable=False)
    estado = relationship("Estado", back_populates="asistentes")

class Estado(Base):
    __tablename__ = 'Estados'
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String,nullable=False)

Estado.asistentes = relationship("Asistente", order_by=Asistente.id, back_populates="estado")