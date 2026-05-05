#!/bin/bash
set -e

echo "========================================="
echo " AMD MI300X & ROCm 7.2 Environment Setup"
echo "========================================="

echo "[1/5] Verifying ROCm Environment & MI300X Visibility..."
rocm-smi
rocminfo | grep -i "MI300X"

echo "[2/5] Updating OS packages and installing build essentials..."
sudo apt-get update
sudo apt-get install -y git build-essential ninja-build

echo "[3/5] Installing PyTorch for ROCm (Nightly/Latest)..."
# Replace with the exact PyTorch ROCm 7.2 wheel once officially available, 
# falling back to the 6.2 nightly which is commonly used currently.
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/rocm6.2

echo "[4/5] Installing Hugging Face Optimum-AMD..."
pip install --upgrade pip
pip install optimum-amd

echo "[5/5] Installing Axolotl (optimized for DeepSpeed & ROCm)..."
if [ ! -d "axolotl" ]; then
    git clone https://github.com/OpenAccess-AI-Collective/axolotl.git
fi
cd axolotl
pip install -e '.[deepspeed]'
cd ..

echo "[6/6] Installing vLLM for ROCm serving..."
pip install vllm

echo "========================================="
echo " Setup Complete! You are ready to train."
echo "========================================="
