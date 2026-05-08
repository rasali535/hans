---
title: ForgeSight
emoji: 🔍
colorFrom: red
colorTo: gray
sdk: docker
pinned: true
license: mit
short_description: "Multimodal QC Copilot · AMD MI300X · Qwen2-VL"
tags:
  - amd
  - rocm
  - mi300x
  - qwen
  - qwen2-vl
  - vllm
  - quality-control
  - agents
  - multimodal
  - industrial-ai
  - vision
---

# 🔍 ForgeSight — Multimodal Quality-Control Copilot

### ⚡ Live Status (Hackathon Mode)
- **Primary Inference**: AMD Instinct MI300X (192GB VRAM)
- **Backend**: FastAPI + vLLM on ROCm
- **Status**: ✅ **ONLINE** (Live Inference Active)
- **Current Server**: `165.245.137.80` (vLLM via Token Auth)

> **AMD + lablab.ai Hackathon** — Track 2 (AMD Developer Cloud) · Track 1 (AI Agents) · Track 3 (Vision & Multimodal AI)

ForgeSight is a production-ready AI system that performs automated visual quality control on the **AMD Instinct MI300X** GPU. Upload a product image and a 4-agent agentic pipeline delivers a structured defect report in seconds.

---

## 🤖 Qwen2-VL — The Brain of ForgeSight

ForgeSight is powered entirely by **[Qwen/Qwen2-VL-7B-Instruct](https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct)**, Alibaba Cloud's state-of-the-art multimodal vision-language model.

### Why Qwen2-VL?

| Capability | How ForgeSight uses it |
| --- | --- |
| **Image understanding** | Reads raw product images — scratches, cracks, misalignments |
| **Structured JSON output** | Each agent returns typed JSON: verdicts, defect lists, action codes |
| **Long-context reasoning** | Diagnostician agent cross-references inspector findings over 8K tokens |
| **Multilingual** | Operator notes can be submitted in any language |
| **192 GB VRAM on MI300X** | Entire 7B model fits in GPU memory with headroom for 88× concurrent sessions |

### How Qwen2-VL is used across the 4-agent pipeline

```text
Image Input (JPEG/PNG/WEBP)
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│ Agent 1 · INSPECTOR  (Qwen2-VL)                         │
│  → Detects defects, produces verdict: pass / warn / fail│
└──────────────────────┬──────────────────────────────────┘
                       │ inspector_report
                       ▼
┌─────────────────────────────────────────────────────────┐
│ Agent 2 · DIAGNOSTICIAN  (Qwen2-VL)                     │
│  → Classifies root cause, estimates severity            │
└──────────────────────┬──────────────────────────────────┘
                       │ diagnostic_report
                       ▼
┌─────────────────────────────────────────────────────────┐
│ Agent 3 · ACTION  (Qwen2-VL)                            │
│  → Maps defects to priority codes (P0–P3) + actions     │
└──────────────────────┬──────────────────────────────────┘
                       │ action_plan
                       ▼
┌─────────────────────────────────────────────────────────┐
│ Agent 4 · REPORTER  (Qwen2-VL)                          │
│  → Writes a human-readable QC report + social post      │
└─────────────────────────────────────────────────────────┘
        │
        ▼
Structured JSON → React Dashboard
```

---

## 🏗️ Architecture

| Layer | Technology |
| --- | --- |
| **Hardware** | AMD Instinct MI300X · 192 GB HBM3 |
| **Runtime** | ROCm 7.2.1 · PyTorch 2.10 (ROCm build) |
| **Inference** | vLLM 0.20.1 (ROCm wheels) · OpenAI-compatible API |
| **Model** | Qwen/Qwen2-VL-7B-Instruct |
| **Backend** | FastAPI + Gradio · Python 3.12 |
| **Persistence** | MongoDB Atlas (motor async driver) |
| **Frontend** | React 18 · Recharts · Lucide |
| **Deployment** | Hugging Face Spaces (Docker) |

---

## 🚀 Running Locally

```bash
# 1. Start vLLM on your AMD GPU
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2-VL-7B-Instruct \
  --host 0.0.0.0 --port 8000 \
  --allowed-origins '["*"]'

# 2. Set environment variables
export AMD_INFERENCE_URL=http://localhost:8000
export AMD_MODEL_NAME=Qwen/Qwen2-VL-7B-Instruct
export MONGO_URL=mongodb+srv://...   # optional

# 3. Start the backend
pip install -r requirements.txt
python app.py
```

---

## 🎯 Hackathon Track Alignment

- **Track 2 · AMD Developer Cloud** *(primary)*: Real MI300X inference via ROCm/vLLM
- **Track 1 · AI Agents**: 4-agent agentic workflow (Inspector → Diagnostician → Action → Reporter)
- **Track 3 · Vision & Multimodal AI**: Qwen2-VL processing product images for industrial QC
- **Qwen Challenge**: Qwen2-VL-7B-Instruct is the sole model powering all four agents end-to-end
