import os
import sys
import torch

def verify_environment():
    print("========================================")
    print("  MI300X ROCm Environment Verification  ")
    print("========================================")
    
    # Check PyTorch
    print(f"\n[1] PyTorch Version: {torch.__version__}")
    if not torch.cuda.is_available():
        print("❌ CUDA/HIP is not available. Please check your ROCm installation.")
        sys.exit(1)
        
    print("✅ PyTorch is installed with CUDA/HIP support.")
    
    # Check ROCm specific device properties
    device_count = torch.cuda.device_count()
    print(f"    Available GPUs: {device_count}")
    for i in range(device_count):
        print(f"    GPU {i}: {torch.cuda.get_device_name(i)}")
        # Check VRAM
        vram = torch.cuda.get_device_properties(i).total_memory / (1024 ** 3)
        print(f"    VRAM GPU {i}: {vram:.2f} GB")
        if "MI300" in torch.cuda.get_device_name(i):
            print("    ✅ MI300X detected.")

    # Check DeepSpeed
    print("\n[2] Checking DeepSpeed...")
    try:
        import deepspeed
        print(f"✅ DeepSpeed Version: {deepspeed.__version__}")
    except ImportError:
        print("❌ DeepSpeed is not installed.")
        
    # Check Flash Attention
    print("\n[3] Checking Flash Attention 2 (ROCm)...")
    try:
        import flash_attn
        print(f"✅ Flash Attention 2 Version: {flash_attn.__version__}")
    except ImportError:
        print("❌ Flash Attention 2 is not installed or not configured for ROCm.")
        
    # Check Axolotl
    print("\n[4] Checking Axolotl...")
    try:
        import axolotl
        print("✅ Axolotl is installed.")
    except ImportError:
        print("❌ Axolotl is not installed.")

    print("\n========================================")
    print("          Verification Complete           ")
    print("========================================")

if __name__ == "__main__":
    verify_environment()
