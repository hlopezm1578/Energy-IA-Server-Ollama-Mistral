from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_ollama import ChatOllama
from typing import List
from pydantic import BaseModel
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.vectorstores.pgvector import PGVector
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts.prompt import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import AIMessage, HumanMessage,SystemMessage,AIMessageChunk
from fastapi.responses import StreamingResponse

import redis
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

r = redis.Redis(host='localhost', port=6379, db=0)
chat = ChatOllama(model="mistral",temperature=0)

embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
CONNECTION_STRING = "postgresql+psycopg2://admin:admin@127.0.0.1:5433/vectordb"
COLLECTION_NAME = "vectordb_bienestar"

vectorstore = PGVector(
    connection_string=CONNECTION_STRING,
    embedding_function=embedding_function,
    collection_name=COLLECTION_NAME,
)

retriever = vectorstore.as_retriever()
chat = ChatOllama(model="mistral",temperature=0,stream=True)
rephrase_template = """Dada la siguiente conversación y una pregunta de seguimiento,
reformule la pregunta de seguimiento para que sea una pregunta independiente, en su idioma original..

Historial de chat:
{chat_history}
Entrada de seguimiento: {question}
Pregunta independiente:"""

REPHRASE_TEMPLATE = PromptTemplate.from_template(rephrase_template)
rephrase_chain = REPHRASE_TEMPLATE | chat | StrOutputParser()

template = """Como un asistente del departamento de Bienestar del Ministerio de energia, 
Responde la pregunta lo mas completa posible, no menciones el contexto ni el origen de los datos, basándose únicamente en el siguiente contexto:

{context}

Pregunta: {question}
"""
ANSWER_PROMPT = ChatPromptTemplate.from_template(template)

retrieval_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | ANSWER_PROMPT
    | chat
    | StrOutputParser()
)

final_chain = rephrase_chain | retrieval_chain

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

@app.get("/test")
def read_root(prompt: str):
    resp =  chat.invoke(prompt)
    return {"respuseta": resp.content}

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

async def generate_chat_responses(message):
    yield "event: start\ndata: Stream iniciado\n\n"

    async for chunk in final_chain.astream(message):
            content = chunk.replace("\n", "<br>")
            yield f"data: {content}\n\n"
    yield "event: end\ndata: Stream Finalizado\n\n"

@app.get("/api/chat_stream")
async def chat_stream(conversation_id: str):
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
    return StreamingResponse(generate_chat_responses(message=message), media_type="text/event-stream")