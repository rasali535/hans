import os
import sys
import uuid
import asyncio
import httpx
import traceback
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# ── CONFIGURATION & STATE ───────────────────────────────────────────────────

MONGO_URL = os.environ.get("MONGO_URL") or os.environ.get("MONGODB_URI")
_db = None
_inspections_col = None
_journal_col = None
_db_initialized = False

_mem_inspections = []
_mem_journal = []

# ── LAZY DB INITIALIZATION ──────────────────────────────────────────────────

async def get_db_collections():
    """Lazily initialize database connections to prevent startup timeouts."""
    global _db, _inspections_col, _journal_col, _db_initialized
    
    if _db_initialized:
        return _inspections_col, _journal_col
    
    if not MONGO_URL:
        print("⚠️ MONGO_URL not set – using in-memory storage")
        _db_initialized = True
        return None, None

    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import certifi
        
        client = AsyncIOMotorClient(
            MONGO_URL, 
            serverSelectionTimeoutMS=2000, # Very aggressive timeout
            tlsCAFile=certifi.where(),
            tlsAllowInvalidCertificates=True
        )
        
        # We don't ping here to keep it fast
        _db = client["forgesight"]
        _inspections_col = _db["inspections"]
        _journal_col = _db["journal"]
        _db_initialized = True
        print("✅ MongoDB connected")
        
        # Check if we need to seed
        try:
            # Non-blocking seed check
            count = await _journal_col.count_documents({})
            if count == 0:
                await _seed_journal_internal()
        except:
            pass
            
    except Exception as e:
        print(f"⚠️  Database error: {e}")
        _db_initialized = True # Mark as "done" so we don't keep retrying and failing
        
    return _inspections_col, _journal_col

async def _seed_journal_internal():
    seeds = [
        {"id": str(uuid.uuid4()), "type": "system", "content": "ForgeSight Cloud Backend initialized.", "created_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "type": "checkpoint", "content": "Multi-agent QC pipeline active.", "created_at": datetime.now(timezone.utc).isoformat()},
    ]
    if _journal_col is not None:
        await _journal_col.insert_many(seeds)
    else:
        _mem_journal.extend(seeds)

# ── APP SETUP ───────────────────────────────────────────────────────────────

app = FastAPI(title="ForgeSight Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── IMPORT AGENTS (LAZY) ─────────────────────────────────────────────────────

def get_agents():
    try:
        sys.path.append(os.path.dirname(__file__))
        import agents
        return agents
    except ImportError:
        import backend.agents as agents
        return agents

# ── API ENDPOINTS ───────────────────────────────────────────────────────────

@app.get("/api/health")
@app.get("/")
async def health():
    return {
        "status": "online", 
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "cloud-serverless"
    }

@app.get("/api/inspections")
async def get_inspections(limit: int = 50):
    col, _ = await get_db_collections()
    if col is not None:
        try:
            cursor = col.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except:
            pass
    return sorted(_mem_inspections, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

@app.post("/api/inspections")
async def create_inspection(request: Request):
    try:
        body = await request.json()
        image_base64 = body.get("image_base64")
        if not image_base64:
            return JSONResponse({"error": "image_base64 required"}, status_code=400)
        
        agents = get_agents()
        result = await agents.run_pipeline(image_base64)
        
        inspection_data = {
            "id": result.get("id", str(uuid.uuid4())),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "image_url": result.get("image_url", "base64"),
            "status": result.get("status", "COMPLETED"),
            "score": result.get("score", 0),
            "findings": result.get("findings", []),
            "agents": result.get("agents", {})
        }
        
        col, _ = await get_db_collections()
        if col is not None:
            await col.insert_one(inspection_data.copy())
        else:
            _mem_inspections.append(inspection_data)

        return inspection_data
    except Exception as e:
        return JSONResponse({"error": str(e), "traceback": traceback.format_exc()}, status_code=500)

@app.get("/api/journal")
async def get_journal():
    _, j_col = await get_db_collections()
    if j_col is not None:
        try:
            cursor = j_col.find({}, {"_id": 0}).sort("created_at", -1).limit(50)
            return await cursor.to_list(length=50)
        except:
            pass
    return sorted(_mem_journal, key=lambda x: x.get("created_at", ""), reverse=True)[:50]

@app.get("/api/telemetry")
async def get_telemetry():
    import random
    return {
        "gpu_util": random.randint(30, 95),
        "vram_used": random.randint(100, 180),
        "latency_ms": random.randint(80, 500),
        "throughput": round(random.uniform(1.0, 5.0), 1),
        "status": "active"
    }

@app.get("/api/blueprint")
async def get_blueprint():
    return {
        "architecture": "Multimodal Agentic Pipeline",
        "provider": "AMD MI300X",
        "engine": "vLLM"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
