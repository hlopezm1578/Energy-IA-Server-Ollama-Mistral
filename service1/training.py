from langchain_community.document_loaders import DirectoryLoader, TextLoader,PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.vectorstores.pgvector import PGVector
import os
import aiofiles

class Training:
    async def crear_archivo_inicial(self,asistente_id,departamento):
        directorio_data = os.path.join("DATA", f"asistente_{asistente_id}")
        os.makedirs(directorio_data, exist_ok=True)
        nombre_archivo = f"{asistente_id}_inicial.txt"
        ruta_archivo = os.path.join(directorio_data, nombre_archivo)
        contenido = f"Soy un asistente virtual del departamento de {departamento}, estoy para responder a sus consultas"
        async with aiofiles.open(ruta_archivo, "w", encoding="utf-8") as archivo:
            await archivo.write(contenido)
    
    async def delete_previous_data(self,asistente_id):
        embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        CONNECTION_STRING = "postgresql+psycopg2://admin:admin@127.0.0.1:5433/vectordb"
        COLLECTION_NAME = f"vectordb_{asistente_id}"
        vectorstore = PGVector(
        connection_string=CONNECTION_STRING,
        embedding_function=embedding_function,
        collection_name=COLLECTION_NAME,
        )
        vectorstore.delete_collection()

    async def proceso(self,asistente_id,chunk,overlap):
        loader = DirectoryLoader(
        f"./DATA/asistente_{asistente_id}", glob="**/*.txt", loader_cls=Utf8TextLoader, show_progress=True
        )
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk,
            chunk_overlap=overlap,
            length_function=len,
            is_separator_regex=False,
        )
        chunks = text_splitter.split_documents(docs)
        embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        CONNECTION_STRING = "postgresql+psycopg2://admin:admin@127.0.0.1:5433/vectordb"
        COLLECTION_NAME = f"vectordb_{asistente_id}"
        vectorstore = PGVector(
        connection_string=CONNECTION_STRING,
        embedding_function=embedding_function,
        collection_name=COLLECTION_NAME,
        )
        vectorstore.add_documents(chunks)

    async def procesoPdf(self,asistente_id,chunk,overlap):
        directorio = f"./DATA/asistente_{asistente_id}"
        pdf_files = [f for f in os.listdir(directorio) if f.endswith('.pdf')]
        documentos = []
        for pdf_file in pdf_files:
            ruta_pdf = os.path.join(directorio, pdf_file)
            loader = PyPDFLoader(ruta_pdf)
            documentos.extend(loader.load())

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk,
            chunk_overlap=overlap,
            length_function=len,
            is_separator_regex=False,
        )
        chunks = text_splitter.split_documents(documentos)
        embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        CONNECTION_STRING = "postgresql+psycopg2://admin:admin@127.0.0.1:5433/vectordb"
        COLLECTION_NAME = f"vectordb_{asistente_id}"
        vectorstore = PGVector(
        connection_string=CONNECTION_STRING,
        embedding_function=embedding_function,
        collection_name=COLLECTION_NAME,
        )
        vectorstore.add_documents(chunks)    


class Utf8TextLoader(TextLoader):
    def __init__(self, *args, **kwargs):
        kwargs['encoding'] = 'utf-8'
        super().__init__(*args, **kwargs)   
    