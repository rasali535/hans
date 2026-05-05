import torch
from transformers import Qwen2VLForConditionalGeneration, AutoTokenizer, AutoProcessor
from PIL import Image

def analyze_construction_site(image_path: str, device: str = "cuda") -> str:
    """
    Uses Qwen2-VL (Track 3) to process a construction site image (e.g., from a drone) 
    and output a structured technical description. This description acts as the 'Context' 
    for the fine-tuned Track 2 Compliance Auditor model.
    """
    # Initialize the model and processor
    # We use a placeholder path for the Qwen2-VL model here.
    model_id = "Qwen/Qwen2-VL-7B-Instruct"
    
    print(f"Loading {model_id} on {device}...")
    try:
        model = Qwen2VLForConditionalGeneration.from_pretrained(
            model_id, 
            torch_dtype=torch.bfloat16, 
            device_map=device
        )
        processor = AutoProcessor.from_pretrained(model_id)
    except Exception as e:
        print(f"Model loading failed (this is expected if weights aren't downloaded): {e}")
        # Return a mocked structured output for demonstration purposes in the hackathon
        return _mocked_vision_output()

    # Load the image
    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as e:
        raise ValueError(f"Could not load image at {image_path}: {e}")

    # Prepare the prompt tailored for technical extraction
    prompt = (
        "You are an expert construction site inspector. Describe the structural elements, "
        "materials, and construction practices visible in this image. Focus on technical "
        "details like concrete pouring, rebar placement, structural steel connections, "
        "and any visible environmental exposure factors. Be highly descriptive and objective."
    )
    
    # Qwen2-VL format
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt},
            ],
        }
    ]
    
    # Preprocess inputs
    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = processor.image_processor(image), None
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to(device)

    # Generate output
    print("Analyzing image...")
    with torch.no_grad():
        generated_ids = model.generate(**inputs, max_new_tokens=256)
        
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]
    
    return _format_for_track2(output_text)

def _mocked_vision_output() -> str:
    """Provides a mocked output when running without the heavy VLM weights."""
    mocked_description = (
        "A bridge pier is constructed using concrete. Reinforcement bars are visible with approximately "
        "50mm of concrete cover. The pier is located directly in a tidal splash zone (marine environment). "
        "Concrete surface appears to have minor honeycombing at the base."
    )
    return _format_for_track2(mocked_description)

def _format_for_track2(vision_text: str) -> str:
    """
    Structures the vision output so it can be seamlessly passed 
    as input 'Context' to the fine-tuned 35B model.
    """
    structured_context = (
        "### VISUAL INSPECTION REPORT (TRACK 3)\n"
        f"{vision_text}\n\n"
        "### TASK\n"
        "Based on the visual inspection report above, identify any violations of structural codes "
        "(e.g., Eurocodes, ASTM, ISO 9001). Provide a label of 'Compliant' or 'Non-Compliant' "
        "followed by a detailed reasoning trace."
    )
    return structured_context

if __name__ == "__main__":
    # Test the pipeline
    test_image = "dummy_construction_site.jpg"
    print(f"Testing Multimodal Pipeline with {test_image}")
    try:
        context_for_track2 = analyze_construction_site(test_image)
        print("\n--- Structured Output for Track 2 Model ---\n")
        print(context_for_track2)
        print("\n-------------------------------------------\n")
    except Exception as e:
        print(f"Error: {e}")
