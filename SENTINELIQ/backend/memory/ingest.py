# memory/ingest.py
# Called after every successful audit — stores vulnerability + patch into ChromaDB

from langchain.schema import Document
from memory.vector_store import get_vectordb
from datetime import datetime
import sqlite3, json, os

DB_PATH = "database/vulnerabilities.db"

# ── SQLite setup (run once) ──────────────────────────────────
def init_sqlite():
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vulnerabilities (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            repo        TEXT,
            pr_number   INTEGER,
            vuln_type   TEXT,
            original    TEXT,
            patch       TEXT,
            test_passed INTEGER,
            timestamp   TEXT
        )
    """)
    conn.commit()
    conn.close()

# ── Store one audit record ───────────────────────────────────
def store_vulnerability(record: dict):
    """
    record = {
        "repo":        "org/payment-service",
        "pr_number":   47,
        "vuln_type":   "SQL Injection",
        "original":    "the vulnerable code string",
        "patch":       "the fixed code string",
        "test_passed": True
    }
    Stores into BOTH ChromaDB (for similarity search) and SQLite (for analytics).
    """

    # 1. Store in ChromaDB for RAG retrieval
    vectordb = get_vectordb()
    doc = Document(
        page_content=record["original"],   # ← the code that gets embedded
        metadata={
            "repo":        record["repo"],
            "pr_number":   str(record["pr_number"]),
            "vuln_type":   record["vuln_type"],
            "patch":       record["patch"],
            "test_passed": str(record["test_passed"]),
            "timestamp":   datetime.utcnow().isoformat()
        }
    )
    vectordb.add_documents([doc])
    vectordb.persist()
    print(f"Stored in ChromaDB: {record['vuln_type']} from {record['repo']}")

    # 2. Store in SQLite for dashboard analytics
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO vulnerabilities (repo, pr_number, vuln_type, original, patch, test_passed, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        record["repo"], record["pr_number"], record["vuln_type"],
        record["original"], record["patch"],
        int(record["test_passed"]), datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()
    print(f"Stored in SQLite: PR #{record['pr_number']}")

# Run this once on startup
init_sqlite()