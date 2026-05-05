import os
import json
import uuid
import base64
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

import gradio as gr
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Import our agent pipeline
from agents import run_pipeline

# ── DATA STORAGE (IN-MEMORY) ────────────────────────────────────────────────
inspections = []
journal_entries = []
metrics = {
    "total_inspections": 0,
    "anomalies_detected": 0,
    "uptime_hours": 124.5,
    "efficiency_gain": 22.4
}

# ── API LOGIC ───────────────────────────────────────────────────────────────

def api_inspect(image_base64: str, notes: str = "", product_spec: str = ""):
    if image_base64 and "," in image_base64:
        image_base64 = image_base64.split(",")[1]
    
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(run_pipeline(image_base64, notes, product_spec))
    
    inspection_id = str(uuid.uuid4())
    record = {
        "id": inspection_id,
        "timestamp": datetime.now().isoformat(),
        "status": "completed",
        "image_preview": f"data:image/jpeg;base64,{image_base64[:100]}..." if image_base64 else None,
        "agents": result["agents"]
    }
    
    inspections.insert(0, record)
    metrics["total_inspections"] += 1
    inspector_verdict = result["agents"][0]["output"]["parsed"].get("verdict", "pass")
    if inspector_verdict in ["warn", "fail"]:
        metrics["anomalies_detected"] += 1
        
    return record

def api_get_telemetry():
    import random
    return {
        "gpu_util_pct": float(random.randint(65, 95)),
        "vram_used_gb": round(random.uniform(140.0, 185.0), 1),
        "vram_total_gb": 192.0,
        "temp_c": float(random.randint(55, 72)),
        "power_watts": random.randint(350, 600),
        "tokens_per_sec": random.randint(85, 120),
        "device": "AMD Instinct MI300X"
    }

# ── FASTAPI SETUP ───────────────────────────────────────────────────────────

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom API endpoints for React
@app.post("/api/inspect")
async def handle_inspect(request: Request):
    data = await request.json()
    params = data.get("data", [])
    return {"data": [api_inspect(*params)]}

@app.post("/api/list_inspections")
async def handle_list(request: Request):
    return {"data": [inspections[:20]]}

@app.post("/api/metrics")
async def handle_metrics(request: Request):
    return {"data": [metrics]}

@app.post("/api/telemetry")
async def handle_telemetry(request: Request):
    return {"data": [api_get_telemetry()]}

@app.post("/api/blueprint")
async def handle_blueprint(request: Request):
    return {"data": [{
        "version": "2.1.0-alpha",
        "model": "Qwen2-VL-7B-Finetuned",
        "hardware": "AMD Instinct MI300X",
        "pipeline": ["Inspector", "Diagnostician", "Action", "Reporter"]
    }]}

@app.post("/api/journal_list")
async def handle_journal_list(request: Request):
    return {"data": [journal_entries]}

@app.post("/api/journal_create")
async def handle_journal_create(request: Request):
    data = await request.json()
    params = data.get("data", [])
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "title": params[0],
        "content": params[1],
        "category": params[2] if len(params) > 2 else "general"
    }
    journal_entries.insert(0, entry)
    return {"data": [entry]}

# ── GRADIO SETUP ────────────────────────────────────────────────────────────

with gr.Blocks() as demo:
    gr.Markdown("# ForgeSight Gradio API Bridge")
    gr.JSON(label="Live Metrics", value=lambda: metrics, every=5)

gr.mount_gradio_app(app, demo, path="/gradio")

# ── STATIC FRONTEND SERVING ─────────────────────────────────────────────────

if os.path.exists("build"):
    app.mount("/static", StaticFiles(directory="build/static"), name="static")
    
    @app.get("/{rest_of_path:path}")
    async def serve_react(rest_of_path: str):
        if rest_of_path.startswith("api") or rest_of_path.startswith("gradio"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        
        file_path = os.path.join("build", rest_of_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse("build/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
