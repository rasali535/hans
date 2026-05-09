"""
ForgeSight — Hugging Face Spaces Gradio backend.
Wraps the multi-agent pipeline so the React frontend can call it
via the Gradio Client JS SDK or plain HTTP POST to /api/<fn_name>.

Deploy: push this repo to a HF Space (Gradio SDK).
"""
import os
import json
import math
import time
import uuid
import gradio as gr
from datetime import datetime, timezone

# ── Import the agent pipeline ───────────────────────────────────────────────
from agents import run_pipeline, generate_social_post

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
        client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000)
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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── 1. Inspection endpoint ──────────────────────────────────────────────────
async def inspect(image_base64: str, notes: str = "", product_spec: str = "", source: str = "upload"):
    """Run the 4-agent inspection pipeline on a base64 image."""
    # Strip potential data-URI prefix
    if "," in image_base64 and image_base64.strip().startswith("data:"):
        image_base64 = image_base64.split(",", 1)[1]

    transcript = await run_pipeline(
        image_base64=image_base64,
        notes=notes or "",
        product_spec=product_spec or "",
    )

    inspection = {
        "id": str(uuid.uuid4()),
        "created_at": _now_iso(),
        "notes": notes or "",
        "product_spec": product_spec or "",
        "source": source or "upload",
        "transcript": transcript,
    }
    await _db_insert_inspection(inspection)

    summary = _summarize(inspection)
    return json.dumps({
        "id": inspection["id"],
        "created_at": inspection["created_at"],
        "transcript": transcript,
        "summary": summary,
    })


# ── 2. List inspections ─────────────────────────────────────────────────────
async def list_inspections(limit: int = 50):
    docs = await _db_list_inspections(limit)
    items = [_summarize(doc) for doc in docs]
    return json.dumps({"items": items, "total": len(items)})


# ── 3. Metrics ───────────────────────────────────────────────────────────────
async def metrics():
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
    quality_score = 0
    if total > 0:
        quality_score = round(100 * (verdict_counts["pass"] + 0.5 * verdict_counts["warn"]) / total)

    return json.dumps({
        "total_inspections": total,
        "verdict_counts": verdict_counts,
        "avg_confidence": round(avg_conf, 3),
        "top_defects": [{"type": t, "count": c} for t, c in top_defects],
        "quality_score": quality_score,
    })


# ── 4. Telemetry (simulated MI300X) ─────────────────────────────────────────
async def telemetry():
    t = time.time()
    gpu_util = 62 + 30 * math.sin(t / 4.0)
    vram_used = 88 + 20 * math.sin(t / 7.0)
    tokens_per_sec = 2850 + 450 * math.sin(t / 3.0)
    power_w = 620 + 80 * math.sin(t / 5.0)
    temp_c = 58 + 7 * math.sin(t / 6.0)
    return json.dumps({
        "simulated": True,
        "device": "AMD Instinct MI300X",
        "gpu_util_pct": round(max(0, min(100, gpu_util)), 1),
        "vram_used_gb": round(max(0, vram_used), 1),
        "vram_total_gb": 192.0,
        "tokens_per_sec": int(max(0, tokens_per_sec)),
        "power_watts": int(max(0, power_w)),
        "temp_c": round(max(0, temp_c), 1),
        "ts": _now_iso(),
    })


# ── 5. Blueprint ────────────────────────────────────────────────────────────
async def blueprint():
    return json.dumps({
        "stack": [
            {
                "layer": "Hardware",
                "title": "AMD Instinct MI300X",
                "detail": "192 GB HBM3 · 5.3 TB/s memory bandwidth · 8× GPU node",
                "why": "Massive VRAM enables serving 70B-class Qwen-VL models without sharding.",
            },
            {
                "layer": "Runtime",
                "title": "ROCm 6.2",
                "detail": "Open compute runtime · HIP · MIOpen · RCCL",
                "why": "PyTorch + vLLM run natively on MI300X via ROCm.",
            },
            {
                "layer": "Serving",
                "title": "vLLM on ROCm",
                "detail": "PagedAttention · continuous batching · OpenAI-compatible API",
                "why": "High-throughput multimodal inference for the agent pipeline.",
            },
            {
                "layer": "Model",
                "title": "Qwen2-VL-72B (fine-tuned)",
                "detail": "LoRA fine-tune on defect-image + work-order pairs via Optimum-AMD",
                "why": "Domain-specialized vision reasoning beats zero-shot generic VLMs.",
            },
            {
                "layer": "Agents",
                "title": "Inspector → Diagnostician → Action → Reporter",
                "detail": "Sequential multi-agent with structured JSON hand-offs",
                "why": "Interpretable, auditable pipeline for industrial QC.",
            },
            {
                "layer": "Product",
                "title": "ForgeSight Console",
                "detail": "React + FastAPI · live transcript · defect feed · build journal",
                "why": "End-to-end demonstrable app shipped for the hackathon.",
            },
        ],
        "finetune_recipe": {
            "base_model": "Qwen/Qwen2-VL-72B-Instruct",
            "dataset": "ForgeSight-QC-10K (proprietary defect-image ↔ work-order pairs)",
            "method": "QLoRA r=64 · Optimum-AMD · bf16",
            "hardware": "1× MI300X node (8 GPUs)",
            "expected_wall_clock": "~6h for 3 epochs on 10K pairs",
            "serve_with": "vLLM 0.6+ on ROCm",
        },
    })


# ── 6. Journal ──────────────────────────────────────────────────────────────
async def journal_list():
    docs = await _db_list_journal(50)
    # Auto-seed if empty
    if not docs:
        await _seed_journal()
        docs = await _db_list_journal(50)
    return json.dumps({"items": docs, "total": len(docs)})


async def journal_create(title: str, body: str, tags: str = ""):
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    try:
        social = await generate_social_post(title, body)
    except Exception:
        social = {"x_post": "", "linkedin_post": ""}

    entry = {
        "id": str(uuid.uuid4()),
        "created_at": _now_iso(),
        "title": title,
        "body": body,
        "tags": tag_list,
        "x_post": social.get("x_post", ""),
        "linkedin_post": social.get("linkedin_post", ""),
    }
    await _db_insert_journal(entry)
    return json.dumps(entry)


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


# ── Helpers ──────────────────────────────────────────────────────────────────
def _summarize(inspection: dict) -> dict:
    agents = inspection.get("transcript", {}).get("agents", [])
    inspector = next((a for a in agents if a["role"] == "inspector"), None)
    reporter = next((a for a in agents if a["role"] == "reporter"), None)
    action = next((a for a in agents if a["role"] == "action"), None)

    inspector_out = (inspector or {}).get("output", {}).get("parsed", {}) or {}
    reporter_out = (reporter or {}).get("output", {}).get("parsed", {}) or {}
    action_out = (action or {}).get("output", {}).get("parsed", {}) or {}

    defects = inspector_out.get("defects") or []
    return {
        "id": inspection["id"],
        "created_at": inspection["created_at"],
        "verdict": inspector_out.get("verdict", "warn"),
        "confidence": float(inspector_out.get("confidence", 0.0) or 0.0),
        "headline": reporter_out.get("headline") or inspector_out.get("observation", "Inspection complete")[:60],
        "defect_count": len(defects) if isinstance(defects, list) else 0,
        "priority": action_out.get("priority", "P2"),
        "source": inspection.get("source", "upload"),
    }


# ── Health / root check ─────────────────────────────────────────────────────
async def health():
    return json.dumps({
        "service": "forgesight",
        "status": "online",
        "track": "AMD Hackathon — Tracks 1+2+3",
        "runtime": "Hugging Face Spaces (Gradio)",
    })


# ── Build the Gradio app ────────────────────────────────────────────────────
# Each gr.Interface becomes a named API endpoint at /api/<fn_name>
# The React frontend calls these via fetch() to the HF Space URL.

with gr.Blocks(title="ForgeSight — AMD MI300X QC Copilot") as demo:
    gr.Markdown("# 🔍 ForgeSight — Multimodal QC Copilot")
    gr.Markdown("Backend API for the ForgeSight React frontend. Powered by AMD Instinct MI300X + ROCm.")

    # --- API-only endpoints (hidden UI, exposed as /api/...) ---

    # Health check
    health_btn = gr.Button("Health Check", visible=False)
    health_out = gr.Textbox(visible=False)
    health_btn.click(fn=health, inputs=[], outputs=health_out, api_name="health")

    # Inspect
    inspect_img = gr.Textbox(visible=False)
    inspect_notes = gr.Textbox(visible=False)
    inspect_spec = gr.Textbox(visible=False)
    inspect_source = gr.Textbox(visible=False)
    inspect_out = gr.Textbox(visible=False)
    inspect_btn = gr.Button("Inspect", visible=False)
    inspect_btn.click(
        fn=inspect,
        inputs=[inspect_img, inspect_notes, inspect_spec, inspect_source],
        outputs=inspect_out,
        api_name="inspect",
    )

    # List inspections
    list_limit = gr.Number(visible=False, value=50)
    list_out = gr.Textbox(visible=False)
    list_btn = gr.Button("List", visible=False)
    list_btn.click(fn=list_inspections, inputs=[list_limit], outputs=list_out, api_name="list_inspections")

    # Metrics
    metrics_out = gr.Textbox(visible=False)
    metrics_btn = gr.Button("Metrics", visible=False)
    metrics_btn.click(fn=metrics, inputs=[], outputs=metrics_out, api_name="metrics")

    # Telemetry
    telem_out = gr.Textbox(visible=False)
    telem_btn = gr.Button("Telemetry", visible=False)
    telem_btn.click(fn=telemetry, inputs=[], outputs=telem_out, api_name="telemetry")

    # Blueprint
    bp_out = gr.Textbox(visible=False)
    bp_btn = gr.Button("Blueprint", visible=False)
    bp_btn.click(fn=blueprint, inputs=[], outputs=bp_out, api_name="blueprint")

    # Journal list
    jl_out = gr.Textbox(visible=False)
    jl_btn = gr.Button("Journal List", visible=False)
    jl_btn.click(fn=journal_list, inputs=[], outputs=jl_out, api_name="journal_list")

    # Journal create
    jc_title = gr.Textbox(visible=False)
    jc_body = gr.Textbox(visible=False)
    jc_tags = gr.Textbox(visible=False)
    jc_out = gr.Textbox(visible=False)
    jc_btn = gr.Button("Journal Create", visible=False)
    jc_btn.click(
        fn=journal_create,
        inputs=[jc_title, jc_body, jc_tags],
        outputs=jc_out,
        api_name="journal_create",
    )

    # --- Visible demo UI for HF Space visitors ---
    with gr.Tab("🔬 Quick Inspect"):
        gr.Markdown("Upload an image to run the 4-agent QC pipeline.")
        with gr.Row():
            with gr.Column():
                demo_img = gr.Image(type="filepath", label="Product Image")
                demo_notes = gr.Textbox(label="Operator Notes", placeholder="e.g. batch B-124, shift 2")
                demo_spec = gr.Textbox(label="Product Spec", placeholder="e.g. aluminum 6061 bracket")
                demo_run = gr.Button("🚀 Run Inspection", variant="primary")
            with gr.Column():
                demo_result = gr.JSON(label="Pipeline Result")

        async def demo_inspect(img_path, notes, spec):
            if not img_path:
                return {"error": "Please upload an image"}
            import base64
            with open(img_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            raw = await inspect(b64, notes or "", spec or "", "upload")
            return json.loads(raw)

        demo_run.click(fn=demo_inspect, inputs=[demo_img, demo_notes, demo_spec], outputs=demo_result)

    with gr.Tab("📊 Status"):
        gr.Markdown("### Service Status")
        status_btn = gr.Button("Check Status")
        status_out = gr.JSON()
        async def check_status():
            h = json.loads(await health())
            m = json.loads(await metrics())
            return {**h, **m}
        status_btn.click(fn=check_status, inputs=[], outputs=status_out)
    
    with gr.Tab("📐 Architecture"):
        gr.Markdown("### ForgeSight Agentic Pipeline Architecture")
        gr.HTML("""
        <div style="background: #0d0d10; padding: 20px; border: 1px solid #333; border-radius: 8px; font-family: sans-serif;">
            <svg viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg">
                <!-- Data Flow -->
                <rect x="50" y="150" width="120" height="60" rx="4" fill="#141416" stroke="#333" />
                <text x="110" y="185" text-anchor="middle" fill="white" font-size="14">Image Upload</text>
                
                <path d="M 170 180 L 220 180" stroke="#ED1C24" stroke-width="2" marker-end="url(#arrow)" />
                
                <rect x="220" y="150" width="120" height="60" rx="4" fill="#ED1C24" stroke="#ED1C24" />
                <text x="280" y="185" text-anchor="middle" fill="white" font-size="14" font-weight="bold">vLLM / MI300X</text>
                
                <path d="M 340 180 L 390 180" stroke="#ED1C24" stroke-width="2" marker-end="url(#arrow)" />
                
                <!-- Agents -->
                <rect x="390" y="50" width="100" height="40" rx="4" fill="#141416" stroke="#ED1C24" />
                <text x="440" y="75" text-anchor="middle" fill="white" font-size="12">Inspector</text>
                
                <rect x="390" y="120" width="100" height="40" rx="4" fill="#141416" stroke="#ED1C24" />
                <text x="440" y="145" text-anchor="middle" fill="white" font-size="12">Diagnostician</text>
                
                <rect x="390" y="190" width="100" height="40" rx="4" fill="#141416" stroke="#ED1C24" />
                <text x="440" y="215" text-anchor="middle" fill="white" font-size="12">Action</text>
                
                <rect x="390" y="260" width="100" height="40" rx="4" fill="#141416" stroke="#ED1C24" />
                <text x="440" y="285" text-anchor="middle" fill="white" font-size="12">Reporter</text>
                
                <!-- Connections -->
                <path d="M 440 90 L 440 120" stroke="#666" stroke-width="1" />
                <path d="M 440 160 L 440 190" stroke="#666" stroke-width="1" />
                <path d="M 440 230 L 440 260" stroke="#666" stroke-width="1" />
                
                <path d="M 490 155 L 550 155" stroke="#ED1C24" stroke-width="2" marker-end="url(#arrow)" />
                
                <rect x="550" y="130" width="150" height="100" rx="4" fill="#141416" stroke="#333" />
                <text x="625" y="165" text-anchor="middle" fill="white" font-size="14">MongoDB Archival</text>
                <text x="625" y="190" text-anchor="middle" fill="#666" font-size="12">Persistence Layer</text>
                
                <defs>
                    <marker id="arrow" markerWidth="10" markerHeight="10" refX="0" refY="3" orient="auto" markerUnits="strokeWidth">
                        <path d="M0,0 L0,6 L9,3 z" fill="#ED1C24" />
                    </marker>
                </defs>
            </svg>
        </div>
        """)
        gr.Markdown("""
        ### Stack Details
        - **Hardware**: AMD Instinct MI300X (192GB VRAM)
        - **Runtime**: ROCm 6.2 + PyTorch
        - **Inference**: vLLM (OpenAI-compatible)
        - **Persistence**: MongoDB Atlas
        """)


if __name__ == "__main__":
    import asyncio
    # Initialize DB before launching
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_init_db())
    
    demo.launch(server_name="0.0.0.0", server_port=7860)
