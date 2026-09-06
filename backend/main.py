"""Amenda — regulatory change impact engine. Run:  uvicorn main:app --reload"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

import ingest
import notify
from analysis import impact, redline, qa
from scrapers import parliament
from llm import LLMNotConfigured, API_KEY, MODEL

app = FastAPI(title="Amenda")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])

FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")


@app.get("/api/health")
def health():
    return {"ok": True, "llm_configured": bool(API_KEY), "model": MODEL}


@app.get("/api/amendments")
def amendments():
    return impact.load_json("amendments", "amendments.json")


@app.get("/api/watchlist")
def watchlist():
    return parliament.get_watchlist()


@app.get("/api/clients")
def clients():
    data = impact.load_json("clients", "clients.json")
    # list view: omit full document text
    out = []
    for c in data:
        out.append({**c, "documents": [
            {k: d[k] for k in ("id", "name", "added")} for d in c["documents"]
        ], "docCount": len(c["documents"])})
    return out


@app.get("/api/clients/{client_id}")
def client_detail(client_id: str):
    for c in impact.load_json("clients", "clients.json"):
        if c["id"] == client_id:
            return c
    return JSONResponse({"error": "not found"}, status_code=404)


class SweepRequest(BaseModel):
    amendment_ids: list[str]
    client_ids: list[str] | None = None


@app.post("/api/sweep")
def run_sweep(req: SweepRequest):
    try:
        return impact.sweep(req.amendment_ids, req.client_ids)
    except LLMNotConfigured as e:
        return JSONResponse({"error": str(e)}, status_code=503)


class AskRequest(BaseModel):
    question: str
    history: list[dict] = []


@app.post("/api/ask")
def ask(req: AskRequest):
    """Free-text question. Returns an answer, or tells the client to sweep."""
    try:
        amendments = impact.load_json("amendments", "amendments.json")
        clients = impact.load_json("clients", "clients.json")
        route = qa.classify(req.question)
        if route == "sweep":
            return {"route": "sweep"}
        return {"route": "qa",
                "answer": qa.ask(req.question, req.history, amendments, clients)}
    except LLMNotConfigured as e:
        return JSONResponse({"error": str(e)}, status_code=503)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


class RedlineRequest(BaseModel):
    amendment_id: str
    client_id: str
    doc_id: str
    verdict: dict = {}


@app.post("/api/redline")
def make_redline(req: RedlineRequest):
    amendments = {a["id"]: a for a in impact.load_json("amendments", "amendments.json")}
    clients = {c["id"]: c for c in impact.load_json("clients", "clients.json")}
    a, c = amendments.get(req.amendment_id), clients.get(req.client_id)
    if not a or not c:
        return JSONResponse({"error": "Unknown amendment or client"}, status_code=404)
    doc = next((d for d in c["documents"] if d["id"] == req.doc_id), None)
    if not doc:
        return JSONResponse({"error": "Unknown document"}, status_code=404)
    result = redline.propose(a, c, doc, req.verdict)
    if "error" in result:
        return JSONResponse(result, status_code=503)
    return result


class DecisionRequest(BaseModel):
    proposal_id: str
    action: str          # approve | reject | flag
    actor: str = "Tan Wei Ming"
    note: str = ""


@app.post("/api/redline/decide")
def decide_redline(req: DecisionRequest):
    result = redline.decide(req.proposal_id, req.action, req.actor, req.note)
    if "error" in result:
        return JSONResponse(result, status_code=400)
    return result


@app.get("/api/audit")
def audit():
    return {"entries": redline.audit_log(), "proposals": redline.all_proposals()}


# ---- document upload ----
@app.post("/api/clients/{client_id}/documents")
async def upload_document(client_id: str, file: UploadFile = File(...),
                          description: str = Form("")):
    try:
        content = await file.read()
        if len(content) > 15 * 1024 * 1024:
            return JSONResponse({"error": "File too large (max 15MB)."}, status_code=413)
        return ingest.add_document(client_id, file.filename, content, description)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": f"Could not read that file: {e}"}, status_code=500)


class NewClient(BaseModel):
    name: str
    practice: str = ""
    business: str = ""
    headcount: int = 0
    notes: str = ""


@app.post("/api/clients")
def create_client(req: NewClient):
    if not req.name.strip():
        return JSONResponse({"error": "Client name is required."}, status_code=400)
    return ingest.add_client(req.name, req.practice, req.business,
                             req.headcount, req.notes)


# ---- email connector ----
class EmailPrefs(BaseModel):
    email: str
    provider: str = "Outlook"
    cadence: str = "The moment a client is affected"


@app.get("/api/email/prefs")
def email_prefs():
    return notify.get_prefs()


@app.post("/api/email/connect")
def email_connect(req: EmailPrefs):
    if "@" not in req.email:
        return JSONResponse({"error": "Enter a valid work address."}, status_code=400)
    return notify.save_prefs(req.email, req.provider, req.cadence)


class NotifyRequest(BaseModel):
    amendment_id: str
    hits: list = []


@app.post("/api/email/send")
def email_send(req: NotifyRequest):
    prefs = notify.get_prefs()
    if not prefs.get("connected"):
        return JSONResponse(
            {"error": "Connect an email address in Settings first."}, status_code=400)
    amendments = {a["id"]: a for a in impact.load_json("amendments", "amendments.json")}
    a = amendments.get(req.amendment_id)
    if not a:
        return JSONResponse({"error": "Unknown amendment"}, status_code=404)
    subject, body = notify.compose_brief(a, req.hits)
    return notify.send(prefs["email"], subject, body, prefs.get("provider", "Outlook"))


@app.get("/api/email/outbox")
def email_outbox():
    return {"messages": notify.outbox()}


# ---- frontend ----
@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND, "index.html"))


@app.get("/classical.css")
def css():
    return FileResponse(os.path.join(FRONTEND, "src", "assets", "classical.css"))


@app.get("/amenda_icon.png")
def logo():
    return FileResponse(os.path.join(FRONTEND, "src", "assets", "amenda_icon.png"))
