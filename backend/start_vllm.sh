#!/bin/bash
# ============================================================
# ForgeSight — Start vLLM Inference Server on AMD MI300X
# ============================================================
# Default configuration
MODEL_NAME=${AMD_MODEL_NAME:-"Qwen/Qwen2-VL-7B-Instruct"}
PORT=${PORT:-8000}

echo "🚀 Starting vLLM Server with $MODEL_NAME on port $PORT..."

# Use the venv if it exists
if [ -f "/opt/forgesight/venv/bin/activate" ]; then
    source /opt/forgesight/venv/bin/activate
fi

# vLLM on ROCm requires some specific environment variables for best performance
export HSA_OVERRIDE_GFX_VERSION=11.0.0
export NCCL_DEBUG=ERROR

vllm serve "$MODEL_NAME" \
    --host 0.0.0.0 \
    --port "$PORT" \
    --tensor-parallel-size 8 \
    --enable-expert-parallel \
    --mm-encoder-tp-mode data \
    --mm-processor-cache-type shm \
    --reasoning-parser qwen3 \
    --enable-prefix-caching \
    --trust-remote-code
