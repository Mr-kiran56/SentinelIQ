# main.py
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import json, os, sqlite3

from utils.verify import verify_signature
from agent.graph import run_agent
from memory.retriever import search_similar_vulnerabilities
from memory.ingest import store_vulnerability

load_dotenv()
app = FastAPI(title="SentinelIQ API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

audit_results = []   # in-memory store (use Redis in production)

# --- 1. GitHub Webhook ---
@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    sig  = request.headers.get("X-Hub-Signature-256", "")

    if not verify_signature(body, sig):
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = json.loads(body)
    event   = request.headers.get("X-GitHub-Event")

    if event == "pull_request" and payload["action"] in ["opened", "synchronize"]:
        pr_number = payload["pull_request"]["number"]
        repo_name = payload["repository"]["full_name"]
        diff_url  = payload["pull_request"]["diff_url"]
        head_sha  = payload["pull_request"]["head"]["sha"]

        background_tasks.add_task(
            run_agent, pr_number, repo_name, diff_url, head_sha, audit_results
        )

    return {"status": "received"}   # ← instant 200 OK to GitHub


# --- 2. Get all audit results (React polls this) ---
@app.get("/results")
def get_results():
    return audit_results


# --- 3. Dashboard analytics (reads SQLite) ---
@app.get("/stats")
def get_stats():
    conn = sqlite3.connect("database/vulnerabilities.db")
    conn.row_factory = sqlite3.Row

    total   = conn.execute("SELECT COUNT(*) as n FROM vulnerabilities").fetchone()["n"]
    by_type = conn.execute("""
        SELECT vuln_type, COUNT(*) as count
        FROM vulnerabilities
        GROUP BY vuln_type
        ORDER BY count DESC
    """).fetchall()
    success = conn.execute("""
        SELECT ROUND(100.0 * SUM(test_passed) / COUNT(*), 1) as rate
        FROM vulnerabilities
    """).fetchone()["rate"]
    top_repos = conn.execute("""
        SELECT repo, COUNT(*) as count
        FROM vulnerabilities
        GROUP BY repo
        ORDER BY count DESC LIMIT 5
    """).fetchall()

    conn.close()
    return {
        "total_vulnerabilities": total,
        "by_type": [dict(r) for r in by_type],
        "patch_success_rate": success,
        "top_risky_repos": [dict(r) for r in top_repos]
    }


# ── 4. Manual search — test your RAG from browser/Postman ───
@app.post("/search")
async def search_memory(request: Request):
    body = await request.json()
    code = body.get("code", "")
    if not code:
        raise HTTPException(status_code=400, detail="Provide 'code' in request body")

    results = search_similar_vulnerabilities(code, n=3)
    return {"similar_cases": results}


# 5. Manual ingest — add a record without running full audit
class VulnRecord(BaseModel):
    repo: str
    pr_number: int
    vuln_type: str
    original: str
    patch: str
    test_passed: bool

@app.post("/ingest")
def manual_ingest(record: VulnRecord):
    store_vulnerability(record.dict())
    return {"status": "stored", "vuln_type": record.vuln_type}


# --- 6. Health check ----
@app.get("/health")
def health():
    return {"status": "SentinelIQ running"}