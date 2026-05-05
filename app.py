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
from agents import run_pipeline, generate_social_post

# ── DATA STORAGE (IN-MEMORY FOR HF SPACES) ───────────────────────────────────
# In a production app, use MongoDB or a persistent volume.
inspections = []
journal_entries = []

# Initialize with some mock metrics
metrics = {
    "total_inspections": 0,
    "anomalies_detected": 0,
    "uptime_hours": 124.5,
    "efficiency_gain": 22.4
}

# ── API FUNCTIONS ───────────────────────────────────────────────────────────

def api_inspect(image_base64: str, notes: str = "", product_spec: str = ""):
    """Run the 4-agent pipeline and save results."""
    # Handle base64 header if present
    if image_base64 and "," in image_base64:
        image_base64 = image_base64.split(",")[1]
    
    # Run pipeline (calls AMD MI300X)
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(run_pipeline(image_base64, notes, product_spec))
    
    # Create inspection record
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
    
    # Check for anomalies in the inspector's verdict
    inspector_verdict = result["agents"][0]["output"]["parsed"].get("verdict", "pass")
    if inspector_verdict in ["warn", "fail"]:
        metrics["anomalies_detected"] += 1
        
    return record

def api_list_inspections():
    return inspections[:20]

def api_get_metrics():
    return metrics

def api_get_telemetry():
    """Simulate real-time hardware telemetry from AMD MI300X."""
    import random
    return {
        "gpu_utilization": random.randint(65, 95),
        "vram_used_gb": round(random.uniform(140.0, 185.0), 1),
        "vram_total_gb": 192.0,
        "temperature_c": random.randint(55, 72),
        "power_watts": random.randint(350, 600),
        "token_throughput": random.randint(85, 120)
    }

def api_get_blueprint():
    """Return the current QC logic blueprint."""
    return {
        "version": "2.1.0-alpha",
        "model": "Qwen2-VL-7B-Finetuned",
        "hardware": "AMD Instinct MI300X",
        "pipeline": ["Inspector", "Diagnostician", "Action", "Reporter"],
        "last_updated": "2026-05-04T18:00:00Z"
    }

def api_journal_list():
    return journal_entries

def api_journal_create(title: str, content: str, category: str = "general"):
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "title": title,
        "content": content,
        "category": category
    }
    journal_entries.insert(0, entry)
    return entry

# ── FASTAPI + STATIC FRONTEND ───────────────────────────────────────────────

app = FastAPI(title="ForgeSight Backend")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create the Gradio interface for debugging/admin
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🔍 ForgeSight — Gradio API Bridge")
    gr.Markdown("This interface serves as the API gateway for the ForgeSight React frontend.")
    
    with gr.Tab("Status"):
        gr.JSON(label="Current Metrics", value=api_get_metrics)
        gr.JSON(label="Latest Telemetry", value=api_get_telemetry)
    
    with gr.Tab("Agents"):
        input_img = gr.Textbox(label="Image Base64")
        input_notes = gr.Textbox(label="Notes")
        btn = gr.Button("Test Pipeline")
        output = gr.JSON(label="Pipeline Output")
        btn.click(api_inspect, inputs=[input_img, input_notes], outputs=output)

# API Endpoint mapping for the frontend adapter (Gradio style POSTs)
@app.post("/api/inspect")
async def handle_inspect(request: Request):
    data = await request.json()
    params = data.get("data", [])
    result = api_inspect(*params)
    return {"data": [result]}

@app.post("/api/list_inspections")
async def handle_list(request: Request):
    return {"data": [api_list_inspections()]}

@app.post("/api/metrics")
async def handle_metrics(request: Request):
    return {"data": [api_get_metrics()]}

@app.post("/api/telemetry")
async def handle_telemetry(request: Request):
    return {"data": [api_get_telemetry()]}

@app.post("/api/blueprint")
async def handle_blueprint(request: Request):
    return {"data": [api_get_blueprint()]}

@app.post("/api/journal_list")
async def handle_journal_list(request: Request):
    return {"data": [api_journal_list()]}

@app.post("/api/journal_create")
async def handle_journal_create(request: Request):
    data = await request.json()
    params = data.get("data", [])
    result = api_journal_create(*params)
    return {"data": [result]}

# Mount the React build folder at /
# We'll also mount Gradio at /gradio
if os.path.exists("build"):
    app.mount("/static", StaticFiles(directory="build/static"), name="static_files")
    
    @app.get("/")
    async def read_index():
        return FileResponse("build/index.html")

    # Catch-all for React routing (SPA)
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception):
        if not request.url.path.startswith("/api") and not request.url.path.startswith("/gradio"):
            return FileResponse("build/index.html")
        return JSONResponse({"detail": "Not Found"}, status_code=404)

# Mount Gradio
gr.mount_gradio_app(app, demo, path="/gradio")

if __name__ == "__main__":
    import uvicorn
    # Use port 7860 as required by HF Spaces
    uvicorn.run(app, host="0.0.0.0", port=7860)
