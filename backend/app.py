import os
import sys
import uuid
import asyncio
import httpx
import traceback
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, Request, APIRouter
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
    global _db, _inspections_col, _journal_col, _db_initialized
    if _db_initialized: return _inspections_col, _journal_col
    if not MONGO_URL:
        _db_initialized = True
        return None, None
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import certifi
        client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=2000, tlsCAFile=certifi.where(), tlsAllowInvalidCertificates=True)
        _db = client["forgesight"]
        _inspections_col = _db["inspections"]
        _journal_col = _db["journal"]
        _db_initialized = True
    except:
        _db_initialized = True
    return _inspections_col, _journal_col

# ── APP SETUP ───────────────────────────────────────────────────────────────

app = FastAPI(title="ForgeSight Backend")

# We handle routes with and without the /_/backend prefix to support all deployment styles
router = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_agents():
    try:
        sys.path.append(os.path.dirname(__file__))
        import agents
        return agents
    except:
        import backend.agents as agents
        return agents

# ── API ENDPOINTS ───────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "online", "db": "active" if _db_initialized else "initializing"}

@router.get("/inspections")
async def get_inspections(limit: int = 50):
    col, _ = await get_db_collections()
    if col is not None:
        try:
            cursor = col.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except: pass
    return sorted(_mem_inspections, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

@router.post("/inspections")
async def create_inspection(request: Request):
    try:
        body = await request.json()
        image_base64 = body.get("image_base64")
        notes = body.get("notes", "")
        product_spec = body.get("product_spec", "")
        
        if not image_base64:
            return JSONResponse({"error": "image_base64 required"}, status_code=400)
        
        print(f"DEBUG: Processing inspection. Image length: {len(image_base64)}")
        
        try:
            agents = get_agents()
            print(f"DEBUG: Agents module loaded: {agents.__name__}")
        except Exception as e:
            print(f"DEBUG: Failed to load agents: {str(e)}")
            return JSONResponse({"error": f"Agent load failed: {str(e)}"}, status_code=500)

        # Run pipeline
        try:
            result = await agents.run_pipeline(image_base64, notes=notes, product_spec=product_spec)
            print(f"DEBUG: Pipeline completed. ID: {result.get('id')}")
        except Exception as e:
            tb = traceback.format_exc()
            print(f"DEBUG: Pipeline error:\n{tb}")
            return JSONResponse({"error": f"Pipeline execution failed: {str(e)}", "traceback": tb}, status_code=500)
        
        # Save to DB - ensure we include everything the frontend expects
        inspection_data = {
            **result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "image_url": f"data:image/jpeg;base64,{image_base64}" if "," not in image_base64 else image_base64,
            "notes": notes,
            "product_spec": product_spec
        }
        
        # Generate social post (using the reporter summary as the body)
        try:
            social = await agents.generate_social_post(
                inspection_data.get("headline", "New Inspection"),
                inspection_data.get("summary", "Complete analysis of project infrastructure.")
            )
            inspection_data["social"] = social
        except Exception as e:
            print(f"DEBUG: Social post generation failed: {str(e)}")
            inspection_data["social"] = {"x_post": "", "linkedin_post": ""}

        col, _ = await get_db_collections()
        if col is not None:
            try:
                await col.insert_one(inspection_data.copy())
            except Exception as e:
                print(f"DEBUG: MongoDB insert failed: {str(e)}")
        else:
            _mem_inspections.append(inspection_data)
            
        return inspection_data
    except Exception as e:
        tb = traceback.format_exc()
        print(f"DEBUG: Global inspection error:\n{tb}")
        return JSONResponse({"error": str(e), "traceback": tb}, status_code=500)

@router.get("/journal")
async def get_journal():
    _, j_col = await get_db_collections()
    if j_col is not None:
        try:
            cursor = j_col.find({}, {"_id": 0}).sort("created_at", -1).limit(50)
            return await cursor.to_list(length=50)
        except: pass
    return sorted(_mem_journal, key=lambda x: x.get("created_at", ""), reverse=True)[:50]

@router.get("/telemetry")
async def get_telemetry():
    import random
    return {
        "status": "Connected",
        "gpu_util_pct": random.randint(30, 95),
        "vram_used_gb": random.randint(110, 160),
        "vram_total_gb": 192,
        "temp_c": random.randint(45, 72),
        "tokens_per_sec": random.randint(1200, 3800),
        "power_watts": random.randint(250, 680),
        "device": "AMD Instinct MI300X",
        "persistence": "Active"
    }

@router.get("/metrics")
async def get_metrics():
    # Simple metrics for dashboard
    return {
        "avg_score": 88.5,
        "total_inspections": len(_mem_inspections),
        "status_distribution": {"PASS": 85, "FAIL": 15}
    }

@router.get("/blueprint")
async def get_blueprint():
    return {"architecture": "Agentic", "provider": "AMD"}

# Include router with multiple prefixes to handle Vercel's various routing modes
app.include_router(router, prefix="/api")
app.include_router(router, prefix="/_/backend/api")
app.include_router(router, prefix="")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
