from fastapi import FastAPI,Depends,HTTPException
from fastapi.middleware.cors import CORSMiddleware
import services,models,schemas
from db import get_db,engine
from sqlalchemy.orm import Session

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/asistentes/", response_model=list[schemas.Asistente])
def get_all_asistentes(db: Session = Depends(get_db)):
    return services.get_asistente(db)

@app.get("/asistentes/{asistente_id}", response_model=schemas.Asistente)
def get_asistente(asistente_id: int, db: Session = Depends(get_db)):
    asistente = services.get_asistente_by_id(db, asistente_id)
    if asistente is None:
        raise HTTPException(status_code=404, detail="Asistente not found")
    return asistente

@app.post("/asistentes/", response_model=schemas.Asistente)
def create_asistente(asistente: schemas.AsistenteCreate, db: Session = Depends(get_db)):
    return services.create_asistente(db, asistente)

@app.put("/asistentes/{asistente_id}", response_model=schemas.AsistenteCreate)
def update_asistente(asistente_id: int, asistente: schemas.AsistenteCreate, db: Session = Depends(get_db)):
    asistente = services.update_asistente(db, asistente_id, asistente)
    if asistente is None:
        raise HTTPException(status_code=404, detail="Asistente not found")
    return asistente

@app.delete("/asistentes/{asistente_id}", response_model=schemas.Asistente)
def delete_asistente(asistente_id: int, db: Session = Depends(get_db)):
    asistente = services.soft_delete_asistente(db, asistente_id)
    if asistente is None:
        raise HTTPException(status_code=404, detail="Asistente not found")
    return asistente