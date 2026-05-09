# 🔍 ForgeSight: Multimodal QC Copilot

ForgeSight is a high-performance, multi-agent quality control (QC) pipeline designed for industrial and infrastructure inspection. It leverages the massive parallel processing power of the **AMD Instinct MI300X** to run large-scale multimodal models that identify defects, diagnose root causes, and suggest actionable remediation steps in real-time.

---

## 🏗️ Architecture Overview

ForgeSight is built on a distributed "Console-Agent-Compute" architecture:

1.  **ForgeSight Console (Frontend)**: A React-based industrial dashboard built with Tailwind CSS and Radix UI. It provides real-time telemetry from the AMD hardware and an interactive agentic transcript.
2.  **Agentic Backend (Orchestration)**: A FastAPI service (hosted on Hugging Face Spaces) that manages the sequential multi-agent pipeline. It uses Gradio to expose high-performance endpoints to the web.
3.  **MI300X Inference Engine (Compute)**: A dedicated AMD MI300X instance running **ROCm 6.2** and **vLLM**. It serves a fine-tuned **Qwen2-VL-72B** model, providing the "brain" for the multimodal inspections.

---

## 🚀 How We Built It: A Walkthrough

Building ForgeSight was a journey through the cutting edge of AMD hardware and agentic software design. Here is how we did it:

### 1. Fine-Tuning the "Brain" on MI300X
We started by preparing a domain-specific vision model. Using the **Optimum-AMD** library, we fine-tuned **Qwen2-VL-72B** on a proprietary dataset of 10,000 defect-image and work-order pairs.
*   **Hardware**: 1× AMD Instinct MI300X node (8 GPUs).
*   **Method**: QLoRA (r=64) in `bf16` precision.
*   **Outcome**: A model capable of recognizing structural cracks, corrosion, and safety hazards with high precision compared to generic zero-shot models.

### 2. High-Throughput Serving with vLLM & ROCm
To make the agents responsive, we deployed the model using **vLLM** on the **ROCm 6.2** stack.
*   We utilized **PagedAttention** to handle the high VRAM requirements of the 72B model.
*   The massive 192GB VRAM of the MI300X allowed us to serve the full model without sharding, maximizing throughput for our concurrent agent calls.

### 3. Designing the Multi-Agent Pipeline
We implemented a 4-stage sequential pipeline in Python to ensure industrial-grade auditability:
*   **Inspector Agent**: Performs the initial multimodal analysis of the image.
*   **Diagnostician Agent**: Receives the inspection report and determines the root cause (e.g., thermal expansion, improper curing).
*   **Action Agent**: Drafts a prioritized work order with specific remediation steps.
*   **Reporter Agent**: Compiles everything into a human-readable brief for site managers.

### 4. Building the "Build-in-Public" Journal
To track our progress during the hackathon, we integrated a **Social Agent** and a **Build Journal**. Every milestone added to the journal is automatically summarized into punchy social media posts for X and LinkedIn, showcasing the "Build-in-Public" spirit.

### 5. Developing the ForgeSight Console
Finally, we built a premium React frontend.
*   **Live Telemetry**: Real-time visualization of GPU utilization, VRAM usage, and power consumption from the MI300X node.
*   **Agentic Transcripts**: A dynamic UI that displays the "thought process" and JSON hand-offs of each agent in the pipeline.
*   **Data Visualization**: Recharts-powered analytics for defect trends and quality scores.

---

## 🛠️ Tech Stack

*   **Hardware**: AMD Instinct MI300X (192GB HBM3).
*   **Software Stack**: ROCm 6.2, PyTorch, vLLM.
*   **Backend**: FastAPI, Gradio, Python.
*   **Frontend**: React, Tailwind CSS, Radix UI (shadcn/ui), Recharts.
*   **Persistence**: MongoDB (via Motor/Pymongo).

---

## 🏃 Getting Started

### Backend
1. `cd backend`
2. `pip install -r requirements.txt`
3. Configure `.env` with your `AMD_INFERENCE_URL` and `AMD_INFERENCE_TOKEN`.
4. Run `python app.py`.

### Frontend
1. `cd frontend`
2. `npm install`
3. Configure `.env` with your `REACT_APP_BACKEND_URL`.
4. Run `npm start`.

---

*Built for the **AMD Developer Hackathon**.*
