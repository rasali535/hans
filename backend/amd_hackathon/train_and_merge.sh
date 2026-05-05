#!/bin/bash
set -e

echo "========================================="
echo " Training & Merging: MI300X QLoRA"
echo "========================================="

# Ensure the data directory exists and data is generated
if [ ! -f "data/engineering_specs_synthetic.jsonl" ]; then
    echo "Dataset not found. Generating synthetic data..."
    python generate_dataset.py
fi

echo "[1/2] Launching Axolotl Training..."
# We use 'accelerate launch' to properly utilize the MI300X GPUs.
# Ensure you are inside the virtual environment where axolotl is installed.
accelerate launch -m axolotl.cli.train fine-tune.yaml

echo "[2/2] Training Complete. Merging LoRA adapters into Base Model..."
# vLLM performs best when serving a fully merged model rather than loading adapters dynamically.
# Axolotl provides a built-in merging script that outputs the final weights.

export LORA_OUT_DIR="./qwen2.5-32b-engineering-lora"
export MERGED_OUT_DIR="./qwen2.5-32b-engineering-merged"

python -m axolotl.cli.merge_lora fine-tune.yaml \
    --lora_model_dir=$LORA_OUT_DIR \
    --output_dir=$MERGED_OUT_DIR

echo "========================================="
echo " Process Complete!"
echo " Merged model is ready for vLLM deployment at: $MERGED_OUT_DIR"
echo "========================================="
