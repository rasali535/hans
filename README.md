---
title: ForgeSight
emoji: 🔍
colorFrom: red
colorTo: gray
sdk: docker
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

# 🔍 ForgeSight — Multimodal Quality-Control Copilot

This Space hosts the full ForgeSight application:
- **Frontend**: React (served at `/`)
- **Backend**: FastAPI + Gradio (served at `/gradio` and `/api`)
- **Inference**: AMD Instinct MI300X via vLLM

Built for the AMD + lablab Hackathon.
