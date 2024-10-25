from fastapi import FastAPI,Depends,HTTPException,UploadFile,File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import services,schemas
from db import get_db
from sqlalchemy.orm import Session
from typing import List
import httpx
import aiohttp

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

@app.get("/asistentes-enlinea/", response_model=list[schemas.Asistente])
def get_all_asistentes(db: Session = Depends(get_db)):
    return services.get_asistentes_enlinea(db)

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

@app.post("/asistentes/contexto/{asistente_id}")
async def create_documento(asistente_id:int,file: UploadFile = File(...), db: Session = Depends(get_db)):    
    asistente = services.get_asistente_by_id(db, asistente_id)
    if asistente is None:
        raise HTTPException(status_code=404, detail="Asistente not found")
    path = f"./DATA/asistente_{asistente_id}"
    request = schemas.PostDocRequest(asistente_id=asistente_id,path=path)
    url = f"{SERVICE1_URL}/documento?path={path}"  # URL del endpoint en service1
    async with httpx.AsyncClient() as client:
        fileToSave = {'file': (file.filename, file.file, file.content_type)}
        response = await client.post(url,files=fileToSave, json=request.model_dump())
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Error calling training service")
        
        response_data = response.json()
        documento_create =  schemas.DocumentoCreate(
            asistente_id=asistente_id,
            url_archivo=path,
            nombre_archivo=response_data['result'],
            nombre_documento=file.filename,)
        print(documento_create)
        documento = services.create_documento(db,documento_create)
        return documento

@app.get("/asistentes/{asistente_id}/documentos", response_model=List[schemas.Documento])
async def read_documentos(asistente_id: int, db: Session = Depends(get_db)):
    documentos = services.get_documentos_by_asistente_id(db, asistente_id)
    if not documentos:
        #raise HTTPException(status_code=404, detail="No documents found for the given asistente_id")
        return []
    return documentos

@app.get("/asistentes/documentos/{documento_id}", response_model=schemas.Documento)
async def download_documento(documento_id: int, db: Session = Depends(get_db)):
    documento = services.get_documento_by_id(db, documento_id)
    if not documento:
        raise HTTPException(status_code=404, detail="Document not found for the given asistente_id and documento_id")
    return documento

@app.delete("/asistentes/documentos/{documento_id}", response_model=schemas.Documento)
async def delete_documento(documento_id: int, db: Session = Depends(get_db)):
    documento = services.get_documento_by_id(db, documento_id)
    if not documento:
        raise HTTPException(status_code=404, detail="Document not found")

    services.delete_documento(db, documento_id)
    return documento


