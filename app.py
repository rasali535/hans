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
import tempfile
from fpdf import FPDF

# ── Import the agent pipeline ───────────────────────────────────────────────
from agents import run_pipeline, generate_social_post

# ── In-memory store (HF Spaces has no persistent DB) ────────────────────────
# For a real deployment, swap with MongoDB or a HF Dataset-backed store.
_inspections: list = []
_journal: list = []


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
    _inspections.insert(0, inspection)

    summary = _summarize(inspection)
    
    # Generate a simple text-based report path (optional placeholder)
    report_path = _generate_pdf_report(inspection)
    
    return json.dumps({
        "id": inspection["id"],
        "created_at": inspection["created_at"],
        "transcript": transcript,
        "summary": summary,
        "report_url": report_path
    })


# ── 2. List inspections ─────────────────────────────────────────────────────
async def list_inspections(limit: int = 50):
    items = [_summarize(doc) for doc in _inspections[:limit]]
    return json.dumps({"items": items, "total": len(items)})


# ── 3. Metrics ───────────────────────────────────────────────────────────────
async def metrics():
    total = len(_inspections)
    verdict_counts = {"pass": 0, "warn": 0, "fail": 0}
    defect_type_counts = {}
    confidences = []

    for doc in _inspections:
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
    # Auto-seed if empty
    if not _journal:
        await _seed_journal()
    return json.dumps({"items": _journal, "total": len(_journal)})


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
    _journal.insert(0, entry)
    return json.dumps(entry)


async def _seed_journal():
    seeds = [
        {
            "title": "Kickoff: ForgeSight on AMD Developer Cloud",
            "body": "Spun up an MI300X instance on AMD Developer Cloud. First impression: zero CUDA-lock-in, ROCm + PyTorch just worked. Targeting all three hackathon tracks with one agentic multimodal QC copilot.",
            "tags": ["kickoff", "amd", "rocm"],
        },
        {
            "title": "Multi-agent pipeline wired end-to-end",
            "body": "Inspector → Diagnostician → Action → Reporter. Each agent produces strict JSON so hand-offs stay auditable. Running on Claude Sonnet 4.5 today, swapping to Qwen2-VL on MI300X next.",
            "tags": ["agents", "pipeline", "qwen"],
        },
        {
            "title": "Fine-tune recipe: QLoRA on Qwen2-VL with Optimum-AMD",
            "body": "Drafted the LoRA fine-tune path for 10K defect-image ↔ work-order pairs. Expecting ~6h wall-clock on a single MI300X node. vLLM-ROCm will serve the result.",
            "tags": ["fine-tuning", "qlora", "optimum-amd"],
        },
    ]
    for s in seeds:
        try:
            social = await generate_social_post(s["title"], s["body"])
        except Exception:
            social = {"x_post": "", "linkedin_post": ""}
        _journal.insert(0, {
            "id": str(uuid.uuid4()),
            "created_at": _now_iso(),
            **s,
            "x_post": social.get("x_post", ""),
            "linkedin_post": social.get("linkedin_post", ""),
        })


def _generate_pdf_report(inspection: dict) -> str:
    """Generates a PDF report for an inspection and returns the temporary file path."""
    summary = _summarize(inspection)
    transcript = inspection.get("transcript", {})
    agents = transcript.get("agents", [])

    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "ForgeSight Quality Control Report", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 10, f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
    pdf.ln(5)

    # Summary Section
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 10, "1. EXECUTIVE SUMMARY", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(40, 10, "Inspection ID:", border=0)
    pdf.cell(100, 10, summary["id"], ln=True)
    pdf.cell(40, 10, "Verdict:", border=0)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(100, 10, summary["verdict"].upper(), ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(40, 10, "Confidence:", border=0)
    pdf.cell(100, 10, f"{summary['confidence']:.2%}", ln=True)
    pdf.cell(40, 10, "Headline:", border=0)
    pdf.multi_cell(150, 10, summary["headline"])
    pdf.ln(5)

    # Agent Findings
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "2. MULTI-AGENT ANALYSIS", ln=True, fill=True)
    for agent in agents:
        role = agent.get("role", "unknown").capitalize()
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(190, 8, f"Agent: {role}", ln=True)
        pdf.set_font("Arial", '', 9)
        output = agent.get("output", {}).get("raw", "No detailed output.")
        # Sanitize for PDF
        output = output.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(190, 6, output)
        pdf.ln(2)

    # Footer
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(190, 10, "Powered by AMD Instinct MI300X + ROCm | ForgeSight Multi-Agent Pipeline", ln=True, align='C')

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp.name)
    return temp.name


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

    with gr.Tab("🏗️ Blueprint"):
        gr.Markdown("### ForgeSight Architecture & Tech Stack")
        bp_view_btn = gr.Button("Fetch Blueprint")
        bp_display = gr.JSON(label="System Specs")
        
        async def get_bp():
            return json.loads(await blueprint())
            
        bp_view_btn.click(fn=get_bp, inputs=[], outputs=bp_display)
        
        gr.Markdown("""
        #### Agent Pipeline Flow
        1. **Inspector**: Vision-reasoning agent identifies defects and assigns a base verdict.
        2. **Diagnostician**: Correlates defects with product specs and historical maintenance data.
        3. **Action Agent**: Determines severity and creates high-priority work orders.
        4. **Reporter**: Generates multi-channel summaries (Social, PDF, Email).
        """)

    with gr.Tab("📋 Inspection Report"):
        gr.Markdown("### Download Inspection Report")
        with gr.Row():
            report_select = gr.Dropdown(label="Select Inspection", choices=[])
            report_refresh = gr.Button("🔄 Refresh List")
        
        report_download = gr.File(label="Download PDF Report")
        
        async def refresh_inspections():
            data = json.loads(await list_inspections())
            choices = [f"{i['id']} - {i['headline'][:30]}..." for i in data["items"]]
            return gr.update(choices=choices)
            
        async def fetch_report(selection):
            if not selection: return None
            iid = selection.split(" - ")[0]
            # Find the inspection in our list
            inspection = next((i for i in _inspections if i["id"] == iid), None)
            if not inspection: return None
            return _generate_pdf_report(inspection)
            
        report_refresh.click(fn=refresh_inspections, inputs=[], outputs=report_select)
        report_select.change(fn=fetch_report, inputs=[report_select], outputs=report_download)


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
