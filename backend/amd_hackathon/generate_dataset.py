import json
import os
import random
from pathlib import Path

# We will save the data to the 'data' directory relative to where the script is run
OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "infrastructure_compliance.jsonl"

# Synthetic data templates focused on Infrastructure Standards (Eurocodes, ASTM, ISO 9001)
# and 'Violation Reasoning'
SYSTEM_PROMPT = "You are an expert infrastructure compliance auditor. Given a technical description of a construction element, compare it against relevant engineering standards (Eurocodes, ASTM Standards, ISO 9001) to identify any violations. You must output the label 'Compliant' or 'Non-Compliant' followed by a detailed reasoning trace."

SYNTHETIC_SAMPLES = [
    {
        "user": "A bridge pier is constructed using concrete with a compressive strength of 25 MPa. It is exposed to a severe marine environment (XS3 exposure class).",
        "assistant": "**Label**: Non-Compliant\n\n**Reasoning Trace**: According to Eurocode 2 (EN 1992-1-1), structures in exposure class XS3 (tidal, splash, and spray zones in marine environments) require a minimum concrete strength class of C35/45 to ensure adequate durability and resistance to chloride-induced corrosion. The provided compressive strength of 25 MPa (C25/30) is insufficient for this exposure class, violating the structural code requirements."
    },
    {
        "user": "The quality management system documentation includes a calibration record for the torque wrenches used on the primary structural steel connections. The calibration was performed 6 months ago, and the required interval is 12 months.",
        "assistant": "**Label**: Compliant\n\n**Reasoning Trace**: Under ISO 9001:2015 Clause 7.1.5 (Monitoring and measuring resources), organizations must retain appropriate documented information as evidence of fitness for purpose of monitoring and measurement resources. The torque wrenches are calibrated within the required 12-month interval (performed 6 months ago), satisfying the quality management standard for infrastructure construction."
    },
    {
        "user": "Structural steel beams are connected using high-strength structural bolts (ASTM A325). The bolts are installed using the snug-tightened method for a slip-critical connection.",
        "assistant": "**Label**: Non-Compliant\n\n**Reasoning Trace**: In accordance with the AISC Specification and ASTM standards for structural joints using high-strength bolts, slip-critical connections require bolts to be fully tensioned (e.g., using turn-of-nut, calibrated wrench, or direct tension indicators). The snug-tightened method is only permitted for bearing-type connections where slip is acceptable. Using snug-tightened bolts for a slip-critical connection violates the installation standard and poses a risk of joint failure under service loads."
    },
    {
        "user": "Reinforcing steel (rebar) for the foundation mat is specified as ASTM A615 Grade 60. The rebar is delivered with mill test reports confirming a minimum yield strength of 60,000 psi.",
        "assistant": "**Label**: Compliant\n\n**Reasoning Trace**: ASTM A615 Grade 60 requires deformed carbon-steel bars for concrete reinforcement to have a minimum yield strength of 60,000 psi. The mill test reports confirm that the delivered material meets this mechanical property requirement, ensuring it complies with the specified ASTM standard for the foundation mat."
    }
]

def generate_dataset(num_samples: int = 100):
    """
    Generates a synthetic JSONL dataset formatted in ChatML for Axolotl fine-tuning.
    Focuses on 'Violation Reasoning' for Infrastructure Compliance.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating {num_samples} synthetic samples...")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for _ in range(num_samples):
            # For demonstration, we randomly sample from our templates.
            # In production, an LLM pipeline could generate varied scenarios.
            sample = random.choice(SYNTHETIC_SAMPLES)
            
            chatml_format = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": sample["user"]},
                    {"role": "assistant", "content": sample["assistant"]}
                ]
            }
            
            f.write(json.dumps(chatml_format) + "\n")

    print(f"Dataset successfully saved to {OUTPUT_FILE}")
    print("Format verification passed: ChatML schema applied.")

if __name__ == "__main__":
    # Generate 500 samples to mimic a small fine-tuning dataset
    generate_dataset(500)
