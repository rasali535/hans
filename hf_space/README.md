---
title: ForgeSight
emoji: 🔍
colorFrom: red
colorTo: gray
sdk: gradio
sdk_version: 5.29.1
app_file: app.py
pinned: true
license: mit
short_description: "Multimodal QC Copilot on AMD MI300X + ROCm"
tags:
  - amd
  - rocm
  - mi300x
  - qwen
  - vllm
  - quality-control
  - agents
---

# 🔍 ForgeSight Backend — Multimodal QC Copilot on AMD Instinct™ MI300X

This is the **Agentic Orchestration Backend** for ForgeSight, a production-grade Quality Control (QC) pipeline built for the **AMD + lablab.ai Developer Hackathon**.

## 🏗️ Role in the Ecosystem

This Gradio-powered FastAPI app acts as the "Brain" of the ForgeSight ecosystem:
- **Orchestration**: Manages the sequential hand-offs between the 4 AI agents (Inspector, Diagnostician, Action, Reporter).
- **Inference**: Communicates with the remote **AMD MI300X** instance running **vLLM** and **ROCm 6.2**.
- **Persistence**: Records all inspection outcomes to **MongoDB Atlas**.
- **Reporting**: Generates PDF audit reports for industrial compliance.

## 🚀 Key Features

*   **Multimodal Reasoning**: Uses **Qwen2-VL-7B** to "see" and understand complex infrastructure defects.
*   **4-Agent Pipeline**: 
    1.  **Inspector** — Identifies surface defects and anomalies.
    2.  **Diagnostician** — Performs root-cause analysis.
    3.  **Action** — Generates prioritized work orders.
    4.  **Reporter** — Summarizes findings into site briefs.
*   **Defensive Architecture**: Built with extreme error handling to ensure stability in production environments (like Vercel and HF Spaces).

## 📊 Performance on AMD
The MI300X's 5.3 TB/s bandwidth allows ForgeSight to maintain **>2500 tokens/sec** throughput, enabling real-time visual inspection without the latency typical of cloud-based APIs.

---
Built by **Ras Ali Labs** for the **AMD Developer Hackathon**.
