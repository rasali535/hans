import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments
)
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer

# AMD ROCm Optimization: Enable TF32 for matrix multiplications on MI300X
torch.backends.cuda.matmul.allow_tf32 = True

def main():
    # 1. Configuration
    # We default to an 8B model, but with 192GB VRAM you can easily bump this to a 70B model!
    model_id = "meta-llama/Meta-Llama-3-8B-Instruct" 
    output_dir = "./mi300x-finetuned-model"
    
    # 2. ROCm/MI300X Specific LoRA Config
    # Using a high rank (R=128) for maximum quality, easily accommodated by the 192GB VRAM
    lora_config = LoraConfig(
        r=128,
        lora_alpha=256,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

    # 3. Load Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    tokenizer.pad_token = tokenizer.eos_token

    # 4. Load Model with Flash Attention 2 (Optimized for ROCm)
    # We load in pure bfloat16. If you use a 70B model, install `bitsandbytes-rocm` 
    # and add `load_in_4bit=True` to utilize QLoRA.
    print(f"Loading {model_id} on MI300X...")
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
        device_map="auto", # Maps to cuda:0 which ROCm routes to gfx942 under the hood
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # 5. Load Dataset (Mocked for the ForgeSight Manufacturing Domain)
    # In production, replace this with your actual HuggingFace dataset
    from datasets import Dataset
    print("Preparing Manufacturing Defect dataset...")
    dataset = Dataset.from_dict({
        "text": [
            "<|system|>You are a manufacturing defect diagnostician.<|user|>Analyze this surface scratch.<|assistant|>The scratch is minor and likely caused during the CNC milling stage. Recalibration recommended."
        ] * 500
    })

    # 6. Training Arguments tailored for the MI300X
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=16, # MI300X's huge memory easily handles large micro-batches to saturate HBM3
        gradient_accumulation_steps=4,
        optim="adamw_torch",
        save_steps=100,
        logging_steps=10,
        learning_rate=2e-4,
        bf16=True, # Native bfloat16 on AMD Instinct
        max_grad_norm=0.3,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        report_to="none",
    )

    # 7. Initialize Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=4096, # Massive context length enabled by the high VRAM
        tokenizer=tokenizer,
        args=training_args,
    )

    # 8. Train!
    print("Starting fine-tuning on AMD Instinct MI300X...")
    trainer.train()
    
    # 9. Save Model
    trainer.model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Fine-tuning complete. Model saved to {output_dir}")

if __name__ == "__main__":
    main()
