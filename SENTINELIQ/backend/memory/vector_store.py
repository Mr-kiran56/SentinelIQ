
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

def get_vectordb():
    """
    Returns a live ChromaDB connection using NVIDIA embeddings.
    Called by both ingest.py (to write) and retriever.py (to read).
    """
    embedding = get_embedding_model()
    vectordb = Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embedding,
        collection_name="sentineliq_vulns"  # named collection
    )
    return vectordb