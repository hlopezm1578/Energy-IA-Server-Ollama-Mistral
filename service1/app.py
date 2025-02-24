from fastapi import FastAPI, UploadFile, File, HTTPException,Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
from langchain.vectorstores.pgvector import PGVector
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts.prompt import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import AIMessage, HumanMessage,SystemMessage,AIMessageChunk
from fastapi.responses import StreamingResponse
from training import Training
from dotenv import load_dotenv
#from langchain_openai import OpenAIEmbeddings
#from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
#from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaEmbeddings

load_dotenv()

import redis
import json
import logging
import os
import aiofiles
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

r = redis.Redis(host='localhost', port=6379, db=0)

def initialize_chat_system(asistente_id:str,departamento:str,entidad:str):
    #embedding_function = OpenAIEmbeddings()
    #embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    embedding_function = OllamaEmbeddings(model="nomic-embed-text")
    CONNECTION_STRING = "postgresql+psycopg2://admin:admin@127.0.0.1:5433/vectordb"
    COLLECTION_NAME = f"vectordb_{asistente_id}"

    vectorstore = PGVector(
    connection_string=CONNECTION_STRING,
    embedding_function=embedding_function,
    collection_name=COLLECTION_NAME,
    )
    retriever = vectorstore.as_retriever()
    #chat = ChatOpenAI(temperature=0,stream=True)
    chat = ChatOllama(model="mistal",temperature=0,stream=True)

    rephrase_template = """Dada la siguiente conversación y una pregunta de seguimiento,
    reformule la pregunta de seguimiento para que sea una pregunta independiente, en su idioma original..

    Historial de chat:
    {chat_history}
    Entrada de seguimiento: {question}
    Pregunta independiente:"""

    REPHRASE_TEMPLATE = PromptTemplate.from_template(rephrase_template)
    rephrase_chain = REPHRASE_TEMPLATE | chat | StrOutputParser()

    template = f"""Eres un asistente virtual del departamento de {departamento} de {entidad}, y estas aquí para ayudar a los usuarios con sus preguntas.
    Responde la pregunta lo mas completa posible, no menciones el contexto ni el origen de los datos, 
    si no hay informacion en el contexto responde 'No tengo información sobre esa consulta', 
    basándose únicamente en el siguiente contexto:

    {{context}}

    Pregunta: {{question}}
    """
    ANSWER_PROMPT = ChatPromptTemplate.from_template(template)

    retrieval_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | ANSWER_PROMPT
        | chat
        | StrOutputParser()
    )

    final_chain = rephrase_chain | retrieval_chain
    return final_chain

ROLE_CLASS_MAP = {
    "asistente": AIMessage,
    "usuario": HumanMessage,
    "system": SystemMessage
}

class Message(BaseModel):
    role: str
    content: str

class Conversation(BaseModel):
    conversation: List[Message]
class TrainingRequest(BaseModel):
    asistente_id: int
    departamento: str
    chunks: int
    overlap: int

class PostDocRequest(BaseModel):
    asistente_id: int
    path:str

def create_messages(conversation):
    return [ROLE_CLASS_MAP[message["role"]](content=message["content"]) for message in conversation]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/training")
async def run_training(request:TrainingRequest):
    try:
        training_instance = Training()
        await training_instance.crear_archivo_inicial(request.asistente_id, request.departamento)
        await training_instance.proceso(request.asistente_id, request.chunks, request.overlap)
        return {"result": "Training completed"}
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/training-model")
async def run_training(request:TrainingRequest):
    training_instance = Training()
    await training_instance.delete_previous_data(request.asistente_id)
    await training_instance.proceso(request.asistente_id, request.chunks, request.overlap)
    await training_instance.procesoPdf(request.asistente_id, request.chunks, request.overlap)
    return {"result": "Training completed"}

@app.post("/documento")
async def upload_documento(path:str,file: UploadFile = File(...)):
    try:
        file_location = path
        print(file_location)
        random_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
        full_path = os.path.join(file_location, random_filename)
        # Verificar si el directorio existe, si no, crearlo
        if not os.path.exists(os.path.dirname(file_location)):
            os.makedirs(os.path.dirname(file_location), exist_ok=True)

        async with aiofiles.open(full_path, "wb") as buffer:
            while content := await file.read(1024):  # Leer el archivo en bloques de 1024 bytes
                await buffer.write(content)
        return {"result": random_filename}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=f"Permission denied: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documento/download/")
async def download_file(file_path: str,filename: str = Query(..., description="Nombre del archivo para la descarga")):
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    async def file_iterator(file_path):
        async with aiofiles.open(file_path, 'rb') as file:
            while content := await file.read(1024):
                yield content

    return StreamingResponse(file_iterator(file_path), media_type='application/octet-stream', headers={"Content-Disposition": f"attachment; filename={filename}"})

@app.delete("/documento")
async def delete_documento(file_path: str):
    # Eliminar el archivo físico
    file_path = file_path  # Asumiendo que el documento tiene un atributo file_path
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"result": "Archivo eliminado"}

@app.get("/api/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    logger.info(f"Retrieving initial id {conversation_id}")
    existing_conversation_json = r.get(conversation_id)
    if existing_conversation_json:
        logger.info(f"Exisiting conversation found for id {conversation_id}")
        existing_conversation = json.loads(existing_conversation_json)
    else:
       existing_conversation = {"conversation": [{"role": "asistente", "content": "Hola, ¿en que puedo ayudarlo?"}]}
    return existing_conversation
    
@app.post("/api/conversation/{conversation_id}")
async def service2(conversation_id: str, conversation: Conversation):
    logger.info(f"Conversation with ID {conversation_id}")
    existing_conversation_json = r.get(conversation_id)
    if existing_conversation_json:
        existing_conversation = json.loads(existing_conversation_json)
    else:
        existing_conversation = {"conversation": [{"role": "asistente", "content": "Hola, ¿en que puedo ayudarlo?"}]}

    existing_conversation["conversation"].append(conversation.dict()["conversation"][-1])
    r.set(conversation_id, json.dumps(existing_conversation))
    return existing_conversation

def serialize_aimessagechunk(chunk):
    """
    Custom serializer for AIMessageChunk objects.
    Convert the AIMessageChunk object to a serializable format.
    """
    if isinstance(chunk, AIMessageChunk):
        return chunk.content
    else:
        raise TypeError(
            f"Object of type {type(chunk).__name__} is not correctly formatted for serialization"
        )

async def generate_chat_responses(message,asistente_id:str,departamento:str,entidad:str):
    yield "event: start\ndata: Stream iniciado\n\n"
    final_chain = initialize_chat_system(asistente_id,departamento,entidad)
    async for chunk in final_chain.astream(message):
            content = chunk.replace("\n", "<br>")
            yield f"data: {content}\n\n"
    yield "event: end\ndata: Stream Finalizado\n\n"

@app.get("/api/chat_stream")
async def chat_stream(conversation_id: str,asistente_id:str, departamento:str,entidad:str):
    logger.info(f"Conversation with ID {conversation_id}")
    existing_conversation_json = r.get(conversation_id)
    if existing_conversation_json:
        existing_conversation = json.loads(existing_conversation_json)
    else:
        existing_conversation = {"conversation": [{"role": "asistente", "content": "Hola, ¿en que puedo ayudarlo?"}]}
    
    conversation = create_messages(conversation=existing_conversation["conversation"])
    query = existing_conversation["conversation"][-1]["content"]
    message = {
        "question": query,
        "chat_history": conversation,
    }
    return StreamingResponse(generate_chat_responses(
        message=message,
        asistente_id=asistente_id,
        departamento=departamento,
        entidad=entidad), media_type="text/event-stream")