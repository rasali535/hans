import os
import uuid
import time
import math
import httpx
import json
import tempfile
import asyncio
from datetime import datetime, timezone
from typing import List, Optional

from typing import List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fpdf import FPDF

# Import our agent pipeline
from agents import run_pipeline, AMD_INFERENCE_URL, AMD_MODEL_NAME, AMD_INFERENCE_TOKEN, generate_social_post

# ── MONGODB PERSISTENCE (optional, falls back to in-memory) ──────────────────
MONGO_URL = os.getenv("MONGO_URL", "")
_db = None
_inspections_col = None
_journal_col = None

# In-memory fallback
_mem_inspections: list = []
_mem_journal: list = []

async def _init_db():
    """Attempt to connect to MongoDB; silently fall back to in-memory if unavailable."""
    global _db, _inspections_col, _journal_col
    if not MONGO_URL:
        print("⚠️ MONGO_URL not set – using in-memory storage")
        return
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import certifi
        client = AsyncIOMotorClient(
            MONGO_URL, 
            serverSelectionTimeoutMS=5000,
            tlsCAFile=certifi.where()
        )
        # Verify connection
        await client.admin.command("ping")
        _db = client["forgesight"]
        _inspections_col = _db["inspections"]
        _journal_col = _db["journal"]
        print("✅ MongoDB connected – persistence enabled")
    except Exception as e:
        print(f"⚠️  MongoDB unavailable ({e}) – using in-memory storage")

async def _db_insert_inspection(doc: dict):
    if _inspections_col is not None:
        await _inspections_col.insert_one({**doc, "_id": doc["id"]})
    else:
        _mem_inspections.insert(0, doc)

async def _db_list_inspections(limit=50) -> list:
    if _inspections_col is not None:
        cursor = _inspections_col.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)
    return _mem_inspections[:limit]

async def _db_insert_journal(doc: dict):
    if _journal_col is not None:
        await _journal_col.insert_one({**doc, "_id": doc["id"]})
    else:
        _mem_journal.insert(0, doc)

async def _db_list_journal(limit=50) -> list:
    if _journal_col is not None:
        cursor = _journal_col.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)
    return _mem_journal[:limit]

# ── HELPERS ───────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _summarize(inspection: dict) -> dict:
    agents = inspection.get("transcript", {}).get("agents", [])
    inspector = next((a for a in agents if a["role"] == "inspector"), None)
    reporter  = next((a for a in agents if a["role"] == "reporter"), None)
    action    = next((a for a in agents if a["role"] == "action"), None)

    inspector_out = (inspector or {}).get("output", {}).get("parsed", {}) or {}
    reporter_out  = (reporter  or {}).get("output", {}).get("parsed", {}) or {}
    action_out    = (action    or {}).get("output", {}).get("parsed", {}) or {}

    defects = inspector_out.get("defects") or []
    return {
        "id":           inspection["id"],
        "created_at":   inspection["created_at"],
        "verdict":      inspector_out.get("verdict", "warn"),
        "confidence":   float(inspector_out.get("confidence", 0.0) or 0.0),
        "headline":     (reporter_out.get("headline") or inspector_out.get("observation", "Inspection complete"))[:60],
        "defect_count": len(defects) if isinstance(defects, list) else 0,
        "priority":     action_out.get("priority", "P2"),
        "source":       inspection.get("source", "upload"),
    }

async def _seed_journal():
    """Seed the journal with initial milestones (instant, no LLM calls)."""
    existing = await _db_list_journal(1)
    if existing:
        return
    seeds = [
        {
            "title": "Kickoff: ForgeSight on AMD Developer Cloud",
            "body": "Spun up an MI300X instance on AMD Developer Cloud. First impression: zero CUDA-lock-in, ROCm + PyTorch just worked.",
            "tags": ["kickoff", "amd", "rocm"],
            "x_post": "🚀 ForgeSight is live! We've officially spun up an AMD Instinct MI300X instance on the Developer Cloud. Zero CUDA-lock-in, just raw ROCm power. #AMDHackathon #ROCm #AIatAMD @lablab @AIatAMD",
            "linkedin_post": "We've officially kicked off ForgeSight for the AMD + lablab.ai Hackathon! We're leveraging the massive 192GB VRAM of the MI300X to build a production-ready QC pipeline. #AI #AMD #Engineering",
        },
        {
            "title": "Multi-agent pipeline wired end-to-end",
            "body": "Inspector → Diagnostician → Action → Reporter. Each agent produces strict JSON so hand-offs stay auditable.",
            "tags": ["agents", "pipeline", "qwen"],
            "x_post": "Our 4-agent pipeline is wired! Inspector → Diagnostician → Action → Reporter. Real-time vision reasoning on MI300X. #AIatAMD #AMDHackathon @lablab",
            "linkedin_post": "Auditability is key in industrial QC. ForgeSight's multi-agent pipeline ensures every decision is grounded in structured data. #QualityControl #Agents",
        },
    ]
    for s in seeds:
        entry = {
            "id": str(uuid.uuid4()),
            "created_at": _now_iso(),
            **s,
        }
        await _db_insert_journal(entry)

# ── API LOGIC ─────────────────────────────────────────────────────────────────

async def api_get_telemetry():
    t = time.time()
    status = "Connected"
    error_msg = None
    
    # FOR HACKATHON DEMO: Simulated data for premium UI visuals
    gpu_util      = 65 + 25 * math.sin(t / 4.0)
    vram_used     = 142.0 + 10 * math.sin(t / 6.0)
    tokens_per_sec = int(2700 + 300 * math.sin(t / 3.0))
    power_w       = int(480 + 50 * math.sin(t / 5.0))

    return {
        "gpu_util_pct":   round(gpu_util, 1),
        "vram_used_gb":   round(vram_used, 1),
        "vram_total_gb":  192.0,
        "temp_c":         round(64 + 4 * math.sin(t / 7.0), 1),
        "power_watts":    power_w,
        "tokens_per_sec": tokens_per_sec,
        "device":         "AMD Instinct MI300X",
        "status":         status,
        "is_simulated":   True,
        "persistence":    "MongoDB" if _inspections_col is not None else "In-Memory",
        "ts":             _now_iso(),
    }

# ── FASTAPI SETUP ─────────────────────────────────────────────────────────────

app = FastAPI(title="ForgeSight API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await _init_db()
    await _seed_journal()

@app.get("/api")
@app.get("/api/health")
async def handle_health():
    return {"status": "online", "service": "forgesight", "db": "connected" if _inspections_col is not None else "memory"}

@app.get("/api/inspections")
async def get_inspections(limit: int = 50):
    docs = await _db_list_inspections(limit)
    items = [_summarize(doc) for doc in docs]
    return {"items": items, "total": len(items)}

@app.post("/api/inspections")
async def create_inspection(request: Request):
    data = await request.json()
    image_base64 = data.get("image_base64", "")
    notes = data.get("notes", "")
    product_spec = data.get("product_spec", "")
    source = data.get("source", "upload")

    if image_base64 and "," in image_base64:
        image_base64 = image_base64.split(",")[1]

    transcript = await run_pipeline(image_base64, notes, product_spec)

    inspection = {
        "id":            str(uuid.uuid4()),
        "created_at":    _now_iso(),
        "notes":         notes or "",
        "product_spec":  product_spec or "",
        "source":        source or "upload",
        "transcript":    transcript,
    }
    await _db_insert_inspection(inspection)
    return inspection

@app.get("/api/inspections/{inspection_id}")
async def get_inspection(inspection_id: str):
    inspection = None
    if _inspections_col is not None:
        inspection = await _inspections_col.find_one({"id": inspection_id}, {"_id": 0})
    else:
        inspection = next((i for i in _mem_inspections if i["id"] == inspection_id), None)
    
    if not inspection:
        return JSONResponse({"detail": "Inspection not found"}, status_code=404)
    return inspection

@app.get("/api/metrics")
async def get_metrics():
    docs = await _db_list_inspections(500)
    total = len(docs)
    verdict_counts = {"pass": 0, "warn": 0, "fail": 0}
    defect_type_counts = {}
    confidences = []

    for doc in docs:
        summary = _summarize(doc)
        v = summary["verdict"] if summary["verdict"] in verdict_counts else "warn"
        verdict_counts[v] += 1
        confidences.append(summary["confidence"])
        agents = doc.get("transcript", {}).get("agents", [])
        inspector = next((a for a in agents if a["role"] == "inspector"), None)
        defects = ((inspector or {}).get("output", {}).get("parsed", {}) or {}).get("defects") or []
        if isinstance(defects, list):
            for d in defects:
                if isinstance(d, dict):
                    t = (d.get("type") or "unknown").lower()
                    defect_type_counts[t] = defect_type_counts.get(t, 0) + 1

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    top_defects = sorted(defect_type_counts.items(), key=lambda x: x[1], reverse=True)[:6]
    quality_score = round(100 * (verdict_counts["pass"] + 0.5 * verdict_counts["warn"]) / total) if total > 0 else 100

    return {
        "total_inspections": total,
        "verdict_counts": verdict_counts,
        "avg_confidence": round(avg_conf, 3),
        "top_defects": [{"type": t, "count": c} for t, c in top_defects],
        "quality_score": quality_score,
    }

@app.get("/api/telemetry")
async def get_telemetry():
    return await api_get_telemetry()

@app.get("/api/blueprint")
async def get_blueprint():
    return {
        "stack": [
            {"layer": "Hardware", "title": "AMD Instinct MI300X", "detail": "192 GB HBM3 · 5.3 TB/s bandwidth", "why": "Enables massive VRAM pools for multimodal Qwen-VL."},
            {"layer": "Runtime", "title": "ROCm 6.2", "detail": "Open compute stack · PyTorch 2.4", "why": "Native AMD acceleration without CUDA lock-in."},
            {"layer": "Serving", "title": "vLLM", "detail": "PagedAttention · continuous batching", "why": "High-throughput serving for agentic chains."},
            {"layer": "Model", "title": "Qwen2-VL-72B", "detail": "Fine-tuned for structural defects", "why": "Domain-specialized vision reasoning."},
            {"layer": "Agents", "title": "Sequential Agentic Chain", "detail": "Structured JSON hand-offs", "why": "Auditability and reliability."},
        ]
    }

@app.get("/api/journal")
async def list_journal():
    items = await _db_list_journal(50)
    if not items:
        await _seed_journal()
        items = await _db_list_journal(50)
    return {"items": items, "total": len(items)}

@app.post("/api/journal")
async def create_journal(request: Request):
    data = await request.json()
    title = data.get("title", "")
    body = data.get("body", "")
    tags = data.get("tags", [])
    
    try:
        social = await generate_social_post(title, body)
    except:
        social = {"x_post": "", "linkedin_post": ""}

    entry = {
        "id": str(uuid.uuid4()),
        "created_at": _now_iso(),
        "title": title,
        "body": body,
        "tags": tags,
        "x_post": social.get("x_post", ""),
        "linkedin_post": social.get("linkedin_post", ""),
    }
    await _db_insert_journal(entry)
    return entry

# Mount Gradio - REMOVED for Vercel deployment to stay under size limits
# app = gr.mount_gradio_app(app, demo, path="/gradio")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
