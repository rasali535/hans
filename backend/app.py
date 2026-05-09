import os
import sys
import uuid
import asyncio
import httpx
import traceback
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Import agent pipeline logic
try:
    # Ensure current directory is in path for Vercel
    sys.path.append(os.path.dirname(__file__))
    from agents import run_pipeline, AMD_INFERENCE_URL, AMD_MODEL_NAME, AMD_INFERENCE_TOKEN, generate_social_post
except ImportError:
    # Fallback if running from root
    from backend.agents import run_pipeline, AMD_INFERENCE_URL, AMD_MODEL_NAME, AMD_INFERENCE_TOKEN, generate_social_post

# ── CONFIGURATION ────────────────────────────────────────────────────────────

MONGO_URL = os.environ.get("MONGO_URL") or os.environ.get("MONGODB_URI")
# Global database references
_db = None
_inspections_col = None
_journal_col = None

# In-memory fallbacks
_mem_inspections = []
_mem_journal = []

# ── APP INITIALIZATION ───────────────────────────────────────────────────────

app = FastAPI(title="ForgeSight Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
            tlsCAFile=certifi.where(),
            tlsAllowInvalidCertificates=True
        )
        _db = client["forgesight"]
        _inspections_col = _db["inspections"]
        _journal_col = _db["journal"]
        print("✅ MongoDB client initialized")
    except Exception as e:
        print(f"⚠️  MongoDB unavailable ({e}) – using in-memory storage")

async def _seed_journal():
    """Seed the journal with initial milestones."""
    try:
        existing = await _db_list_journal(1)
        if existing: return
    except: return

    seeds = [
        {"id": str(uuid.uuid4()), "type": "system", "content": "ForgeSight Backend initialized.", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "type": "checkpoint", "content": "AMD MI300X vLLM pipeline linked.", "created_at": datetime.now(timezone.utc).isoformat()},
    ]
    for s in seeds:
        await _db_insert_journal(s)

@app.on_event("startup")
async def startup_event():
    await _init_db()
    await _seed_journal()

# ── DATABASE HELPERS ────────────────────────────────────────────────────────

async def _db_insert_inspection(data):
    if _inspections_col is not None:
        await _inspections_col.insert_one(data.copy())
    else:
        _mem_inspections.append(data)

async def _db_list_inspections(limit=50):
    if _inspections_col is not None:
        cursor = _inspections_col.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)
    return sorted(_mem_inspections, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

async def _db_insert_journal(data):
    if _journal_col is not None:
        await _journal_col.insert_one(data.copy())
    else:
        _mem_journal.append(data)

async def _db_list_journal(limit=50):
    if _journal_col is not None:
        cursor = _journal_col.find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=limit)
    return sorted(_mem_journal, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]

# ── API ENDPOINTS ───────────────────────────────────────────────────────────

@app.get("/api/health")
@app.get("/api/")
@app.get("/")
async def health():
    return {
        "status": "online", 
        "service": "forgesight", 
        "db": "mongodb" if _inspections_col is not None else "memory",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/inspections")
async def get_inspections(limit: int = 50):
    items = await _db_list_inspections(limit)
    return items

@app.post("/api/inspections")
async def create_inspection(request: Request):
    """Triggers the full multi-agent QC pipeline."""
    try:
        body = await request.json()
        # Frontend uses image_base64, notes, product_spec, source
        image_base64 = body.get("image_base64")
        notes = body.get("notes", "")
        product_spec = body.get("product_spec", "")
        
        if not image_base64:
            return JSONResponse({"error": "image_base64 is required"}, status_code=400)
        
        # Add a journal entry for the start
        await _db_insert_journal({
            "id": str(uuid.uuid4()),
            "type": "process",
            "content": "Starting multimodal inspection via UI upload...",
            "created_at": datetime.now(timezone.utc).isoformat()
        })

        # Run pipeline (assuming run_pipeline can handle base64 or we convert it)
        # For the hackathon demo, we usually pass the raw data or a temp URL
        result = await run_pipeline(image_base64)
        
        # Save to DB
        inspection_data = {
            "id": result.get("id", str(uuid.uuid4())),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "image_url": result.get("image_url", "base64_stored"),
            "status": result.get("status", "COMPLETED"),
            "score": result.get("score", 0),
            "findings": result.get("findings", []),
            "agents": result.get("agents", {}),
            "notes": notes,
            "product_spec": product_spec
        }
        await _db_insert_inspection(inspection_data)

        # Generate social post
        try:
            social = await generate_social_post(inspection_data)
            inspection_data["social"] = social
        except:
            inspection_data["social"] = "Social generation unavailable."

        return inspection_data
    except Exception as e:
        return JSONResponse({"error": str(e), "traceback": traceback.format_exc()}, status_code=500)

@app.get("/api/journal")
async def get_journal():
    items = await _db_list_journal()
    return items

@app.post("/api/journal")
async def create_journal(request: Request):
    body = await request.json()
    entry = {
        "id": str(uuid.uuid4()),
        "type": "user",
        "content": body.get("body", ""),
        "title": body.get("title", ""),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await _db_insert_journal(entry)
    return entry

@app.post("/api/journal/seed")
async def seed_journal_api():
    await _seed_journal()
    return {"status": "seeded"}

@app.get("/api/metrics")
async def get_metrics():
    inspections = await _db_list_inspections(100)
    total = len(inspections)
    if total == 0:
        return {"avg_score": 0, "total_inspections": 0, "status_distribution": {}}
    
    avg_score = sum(i.get("score", 0) for i in inspections) / total
    dist = {}
    for i in inspections:
        s = i.get("status", "UNKNOWN")
        dist[s] = dist.get(s, 0) + 1
        
    return {
        "avg_score": round(avg_score, 2),
        "total_inspections": total,
        "status_distribution": dist,
        "system_load": "nominal"
    }

@app.get("/api/telemetry")
async def get_telemetry():
    """Returns real-time system telemetry (mocked for demo)."""
    import random
    return {
        "gpu_util": random.randint(45, 88),
        "vram_used": random.randint(120, 160), # MI300X 192GB
        "latency_ms": random.randint(120, 450),
        "throughput": round(random.uniform(1.2, 4.5), 1),
        "active_agents": 3,
        "thermal_status": "stable"
    }

@app.get("/api/blueprint")
async def get_blueprint():
    """Returns the system blueprint metadata."""
    return {
        "version": "1.0.0",
        "architecture": "Multimodal Agentic Pipeline",
        "infrastructure": "AMD MI300X vLLM Cluster",
        "agents": ["Inspector", "Analyst", "Social"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
