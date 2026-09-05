"""Amenda — regulatory change impact engine. Run:  uvicorn main:app --reload"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from analysis import impact
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


# ---- frontend ----
@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND, "index.html"))


@app.get("/classical.css")
def css():
    return FileResponse(os.path.join(FRONTEND, "src", "assets", "classical.css"))
