# memory/retriever.py
# Searches ChromaDB for similar past vulnerabilities
# Formats results as context text ready to inject into LLaMA prompt

from memory.vector_store import get_vectordb

def search_similar_vulnerabilities(code: str, n: int = 3) -> list[dict]:
    """
    Takes a code string, finds top-n most semantically similar
    past vulnerabilities from ChromaDB.
    Returns list of metadata dicts.
    """
    vectordb = get_vectordb()
    
    # similarity_search returns Document objects
    results = vectordb.similarity_search_with_score(code, k=n)
    
    cases = []
    for doc, score in results:
        # score is cosine distance — lower = more similar
        if score < 1.2:   # filter out weak matches
            cases.append({
                "vuln_type":  doc.metadata.get("vuln_type", "Unknown"),
                "repo":       doc.metadata.get("repo", "unknown"),
                "original":   doc.page_content,
                "patch":      doc.metadata.get("patch", ""),
                "timestamp":  doc.metadata.get("timestamp", ""),
                "similarity": round(1 - score, 3)   # convert to similarity score
            })
    return cases


def format_context_for_llm(cases: list[dict]) -> str:
    """
    Converts the list of similar cases into clean text
    that gets injected into the LLaMA security analysis prompt.
    """
    if not cases:
        return "No similar past vulnerabilities found. Analyze from scratch."

    lines = ["SIMILAR PAST VULNERABILITIES FROM OUR CODEBASE:\n"]
    for i, c in enumerate(cases, 1):
        lines.append(f"--- Case {i} ({c['vuln_type']} | {c['repo']}) ---")
        lines.append(f"Vulnerable code:\n{c['original'][:300]}")  # truncate long snippets
        lines.append(f"Fix applied:\n{c['patch'][:300]}")
        lines.append(f"Similarity score: {c['similarity']}\n")

    return "\n".join(lines)


def get_rag_context(code: str) -> str:
    """
    One-liner for the LangGraph agent to call.
    Returns formatted context string ready to paste into prompt.
    """
    cases = search_similar_vulnerabilities(code, n=3)
    return format_context_for_llm(cases)