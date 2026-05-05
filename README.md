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

# 🔍 ForgeSight — Multimodal Quality-Control Copilot

ForgeSight ships a **4-agent pipeline** that inspects assembly-line images,
diagnoses root cause, drafts work orders, and publishes reports — fine-tuned
on **Qwen2-VL** and served on **AMD Instinct MI300X** via ROCm + vLLM.

## Architecture

```
React Frontend → HF Spaces (Gradio API) → AMD MI300X vLLM (agents.py)
```

### Agents
1. **Inspector** — Vision analysis, defect detection
2. **Diagnostician** — Root-cause analysis
3. **Action** — Work order generation
4. **Reporter** — Human-readable summary

## Hackathon Tracks
- **Track 1**: Agentic AI on AMD
- **Track 2**: Fine-tuning with Optimum-AMD
- **Track 3**: Multimodal vision (Qwen2-VL)

Built for the AMD + lablab Hackathon.
