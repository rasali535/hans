#!/bin/bash
# ForgeSight AMD MI300X Recovery Script
# Run these commands on your remote AMD machine to restore connectivity.

IP="129.212.189.214"
TOKEN="5vftP0OtijtjVncSQj9OyA2LlQz7IUEe45GODu3bUzBS5AKVi"

echo "Checking Docker containers..."
docker ps -a

echo "Starting rocm container..."
docker start rocm

echo "Starting vLLM server inside rocm container..."
# -d runs in background. 
# We use the proxy path compatibility (host 0.0.0.0, port 8000)
docker exec -d rocm python3 -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2-VL-7B-Instruct \
  --host 0.0.0.0 --port 8000 \
  --trust-remote-code \
  --gpu-memory-utilization 0.9 \
  --max-model-len 4096 \
  --allowed-origins '*'

echo "------------------------------------------------"
echo "Server should be reachable at:"
echo "http://$IP/proxy/8000/v1"
echo "Authentication Token: $TOKEN"
echo "------------------------------------------------"
echo "Verify status with: docker logs rocm"
