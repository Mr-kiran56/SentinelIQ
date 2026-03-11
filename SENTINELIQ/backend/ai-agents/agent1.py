# agent/llm_client.py
# Swap OpenAI for LLaMA via NVIDIA endpoints

from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.schema import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

load_dotenv()

# --- LLaMA 3 via NVIDIA API ----
llm = ChatNVIDIA(
    model="meta/llama-3.1-70b-instruct",  # or llama-3.1-8b-instruct for faster/cheaper
    api_key=os.getenv("NVIDIA_API_KEY"),
    temperature=0,
    max_tokens=2048
)

def analyze_code(original_code: str, rag_context: str) -> list[str]:
    """
    Node 1 of LangGraph — finds vulnerabilities.
    Uses RAG context from ChromaDB to guide LLaMA.
    """
    messages = [
        SystemMessage(content="""You are a senior application security engineer.
Your job is to find ALL security vulnerabilities in code.
Return ONLY a valid JSON array of strings. No explanation. No markdown.
Example output: ["SQL injection on line 12", "hardcoded secret on line 7"]"""),

        HumanMessage(content=f"""
{rag_context}

NOW ANALYZE THIS NEW CODE:
{original_code}

Return ONLY a JSON array of vulnerability descriptions.""")
    ]

    response = llm.invoke(messages).content.strip()

    import json
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # fallback: wrap raw response
        return [response]


def generate_patch(original_code: str, vulnerabilities: list, rag_context: str, error: str = None) -> str:
    """
    Node 2 of LangGraph — generates the secure patch.
    """
    retry_ctx = f"\nYour previous patch failed with this error:\n{error}\nFix this too." if error else ""

    messages = [
        SystemMessage(content="""You are a senior security engineer.
Fix ALL vulnerabilities listed. Return ONLY the corrected Python code.
No markdown. No explanation. Just the fixed code."""),

        HumanMessage(content=f"""
{rag_context}

VULNERABILITIES TO FIX:
{chr(10).join(f'- {v}' for v in vulnerabilities)}
{retry_ctx}

ORIGINAL CODE TO FIX:
{original_code}

Return ONLY the corrected Python code.""")
    ]

    return llm.invoke(messages).content.strip()