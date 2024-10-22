from fastapi import FastAPI,Depends,HTTPException
from fastapi.middleware.cors import CORSMiddleware
import services,models,schemas
from db import get_db,engine
from sqlalchemy.orm import Session
import httpx

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICE1_URL = "http://localhost:8000"

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

@app.post("/asistentes/call-training")
async def call_training(request:schemas.TrainingRequest):
    url = f"{SERVICE1_URL}/training"  # URL del endpoint en service1
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=request.model_dump())
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Error calling training service")
        return response.json()
@app.put("/asistentes/{asistente_id}/change-status")
async def change_status(asistente_id: int, estado_id: int, db: Session = Depends(get_db)):
    asistente = services.change_status_asistente(db, asistente_id, estado_id)
    if asistente is None:
        raise HTTPException(status_code=404, detail="Asistente not found")
    return asistente        