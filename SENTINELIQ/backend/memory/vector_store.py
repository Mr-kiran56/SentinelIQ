
from langchain.vectorstores import Chroma
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

PERSIST_DIR = "vector_db"  # local folder where ChromaDB saves data

def get_embedding_model():
    """
    NVIDIA embeddings — uses your NVIDIA_API_KEY from .env
    Model: nvidia/nv-embedqa-e5-v5 (best for code + text)
    """
    return NVIDIAEmbeddings(
        model="nvidia/nv-embedqa-e5-v5",
        api_key=os.getenv("NVIDIA_API_KEY")
    )

import psycopg2
from pgvector.psycopg2 import register_vector
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("POSTGRES_URL")

def get_connection():
    conn = psycopg2.connect(DB_URL)
    register_vector(conn)
    return conn