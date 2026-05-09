"""
ForgeSight multi-agent quality-control pipeline.
Agents call the fine-tuned model served by vLLM on AMD Instinct MI300X.
Falls back to mock responses if the AMD inference server is unreachable.
"""
import os
import json
import uuid
import re
import asyncio
from typing import Optional, List, Dict, Any

import httpx  # async HTTP — lightweight, no extra deps beyond requirements

# ── AMD vLLM inference endpoint ─────────────────────────────────────────────
# vLLM exposes an OpenAI-compatible API at /v1/chat/completions.
# Set AMD_INFERENCE_URL in your .env to point at the running vLLM server.
# Example: http://165.245.143.46:8000   (direct port — ensure firewall allows it)
# Or use the Jupyter proxy route: http://165.245.143.46/proxy/8000
AMD_INFERENCE_URL = os.environ.get(
    "AMD_INFERENCE_URL",
    "http://129.212.189.214"
).rstrip("/")

# Token for the AMD inference server (if required)
AMD_INFERENCE_TOKEN = os.environ.get(
    "AMD_INFERENCE_TOKEN",
    "5peRa6unb0DdXvzB3Pbck48IgNTDmxeJSUvE4NdnhvW70FcaX"
)

# The model name vLLM is serving (used in the chat/completions request).
# Override with AMD_MODEL_NAME env var if you deploy a different checkpoint.
AMD_MODEL_NAME = os.environ.get("AMD_MODEL_NAME", "Qwen/Qwen2-VL-7B-Instruct")

# Timeout (seconds) to wait for the AMD server before falling back to mock.
AMD_TIMEOUT = float(os.environ.get("AMD_TIMEOUT", "60"))

# ── System prompts ───────────────────────────────────────────────────────────
INSPECTOR_SYSTEM = """You are the INSPECTOR agent of ForgeSight — a multimodal quality-control copilot
running on AMD Instinct MI300X + ROCm. Your job: analyze the submitted construction site, road infrastructure, or housing
image and surface visible structural defects, safety hazards, anomalies, or code violations.

Return ONLY compact JSON with this exact shape (no prose, no code fences):
{
  "verdict": "pass" | "warn" | "fail",
  "confidence": 0.0-1.0,
  "defects": [
    {"type": "short category e.g. structural-crack", "severity": "low|medium|high", "location": "short spatial description", "description": "one sentence"}
  ],
  "observation": "2-3 sentence plain-english summary of what you see"
}
Be precise. If the image shows no construction/infrastructure issues at all, still describe what is visible
and mark verdict "warn" with a defect explaining the mismatch."""


DIAGNOSTICIAN_SYSTEM = """You are the DIAGNOSTICIAN agent of ForgeSight. Given the INSPECTOR's
JSON report and user notes, produce a probable root-cause analysis.

Return ONLY compact JSON:
{
  "probable_cause": "one-sentence most likely cause",
  "contributing_factors": ["factor 1", "factor 2", "factor 3"],
  "affected_process_step": "e.g. concrete pouring, asphalt laying, framing"
}
Be concrete and industry-literate."""


ACTION_SYSTEM = """You are the ACTION agent of ForgeSight. Given the INSPECTOR and DIAGNOSTICIAN
outputs, draft an actionable work order.

Return ONLY compact JSON:
{
  "priority": "P0|P1|P2|P3",
  "assignee_role": "e.g. site-manager, structural-engineer, safety-officer",
  "steps": ["step 1", "step 2", "step 3"],
  "estimated_minutes": integer,
  "parts_or_tools": ["item 1", "item 2"]
}"""


REPORTER_SYSTEM = """You are the REPORTER agent of ForgeSight. Compile a final human-readable
summary of the full inspection in <=70 words. Return ONLY JSON:
{
  "headline": "<=10 word title",
  "summary": "<=70 word paragraph",
  "tags": ["tag1", "tag2", "tag3"]
}"""

SOCIAL_SYSTEM = """You craft punchy Build-in-Public social posts for a hackathon project named
"ForgeSight" — a multimodal agentic quality-control copilot running on AMD Instinct MI300X + ROCm.
Always include hashtags: #AMDHackathon #ROCm #AIatAMD #lablab and mention @AIatAMD and @lablab.
Return ONLY JSON:
{"x_post": "<=260 chars, punchy, 1-2 emojis ok", "linkedin_post": "<=600 chars, narrative, 3 short paragraphs"}"""


# ── JSON extraction ──────────────────────────────────────────────────────────
def _extract_json(raw: str) -> Dict[str, Any]:
    """Best-effort JSON extraction from an LLM response."""
    if not raw:
        return {}
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return {"_raw": raw}


# ── Mock fallbacks ───────────────────────────────────────────────────────────
def _mock_response(name: str) -> Dict[str, Any]:
    """Fallback mock responses when AMD server is unreachable."""
    mocks = {
        "inspector": {
            "verdict": "warn", "confidence": 0.85,
            "defects": [{"type": "concrete-crack", "severity": "medium",
                         "location": "foundation wall, sector B", "description": "Diagonal hairline crack visible"}],
            "observation": "Diagonal crack detected on the concrete foundation. [LOCAL MOCK — AMD server offline]"
        },
        "diagnostician": {
            "probable_cause": "Improper curing or settlement issues. [LOCAL MOCK]",
            "contributing_factors": ["Temperature fluctuation", "Soil settlement"],
            "affected_process_step": "Concrete curing"
        },
        "action": {
            "priority": "P2", "assignee_role": "structural-engineer",
            "steps": ["Assess crack depth", "Apply epoxy injection"],
            "estimated_minutes": 120, "parts_or_tools": ["Epoxy resin", "Measurement gauge"]
        },
        "reporter": {
            "headline": "Foundation Crack Detected [Mock]",
            "summary": "Local mock response — start the AMD vLLM server to use the fine-tuned model.",
            "tags": ["crack", "concrete", "mock"]
        },
        "social": {
            "x_post": "Testing our pipeline #AMDHackathon",
            "linkedin_post": "We are testing our pipeline today..."
        },
    }
    parsed = mocks.get(name, {})
    return {"raw": json.dumps(parsed), "parsed": parsed, "source": "mock (AMD server offline)"}


# ── AMD vLLM call (OpenAI-compatible /v1/chat/completions) ───────────────────
async def _call_amd_vllm(
    system_prompt: str,
    user_text: str,
    image_base64: Optional[str] = None,
) -> Optional[str]:
    """
    Call the vLLM server on the AMD MI300X using its OpenAI-compatible API.
    Supports vision models (image_base64) and text-only calls.
    Returns the assistant message text, or None if the server is unreachable.
    """
    # Build messages array
    if image_base64:
        # Multimodal message with base64 image
        user_content = [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }
            },
            {
                "type": "text",
                "text": user_text
            }
        ]
    else:
        user_content = user_text

    payload = {
        "model": AMD_MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": 1024,
        "temperature": 0.1,  # Low temperature for deterministic structured output
    }

    # Candidate endpoints
    base_url = AMD_INFERENCE_URL.rstrip("/")
    candidates = [
        f"{base_url}/proxy/8000/v1/chat/completions",
        f"{base_url}/proxy/8001/v1/chat/completions",
        f"{base_url}:8000/v1/chat/completions",
        f"{base_url}:8001/v1/chat/completions",
        f"{base_url}/v1/chat/completions",
    ]

    headers = {}
    if AMD_INFERENCE_TOKEN:
        # Try both token and Bearer formats
        headers["Authorization"] = f"token {AMD_INFERENCE_TOKEN}"
    
    last_err = None
    for url in candidates:
        try:
            async with httpx.AsyncClient(timeout=AMD_TIMEOUT) as client:
                # Add token as param too just in case
                test_url = f"{url}?token={AMD_INFERENCE_TOKEN}" if AMD_INFERENCE_TOKEN else url
                resp = await client.post(test_url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                
                # Try Bearer if token failed
                headers["Authorization"] = f"Bearer {AMD_INFERENCE_TOKEN}"
                resp = await client.post(test_url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            last_err = e
            continue
    
    return None  # All candidates failed


# ── Agent runner ─────────────────────────────────────────────────────────────
async def _run_agent(
    name: str,
    system_message: str,
    user_text: str,
    image_base64: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run a single agent. Tries AMD MI300X vLLM first, falls back to mock.
    """
    raw_text = await _call_amd_vllm(system_message, user_text, image_base64)

    if raw_text is None:
        # AMD server not reachable — use local mock (safe for dev/demo)
        result = _mock_response(name)
        return result

    # AMD server responded — parse its JSON output
    parsed = _extract_json(raw_text)
    return {
        "raw": raw_text,
        "parsed": parsed,
        "source": f"AMD MI300X vLLM @ {AMD_INFERENCE_URL} ({AMD_MODEL_NAME})"
    }


# ── Public pipeline ──────────────────────────────────────────────────────────
async def run_pipeline(
    image_base64: str,
    notes: str = "",
    product_spec: str = "",
) -> Dict[str, Any]:
    """
    Run the 4-agent pipeline sequentially and return the full transcript.
    """
    context = f"Operator notes: {notes or '(none)'}\nProduct spec: {product_spec or '(generic)'}"

    # 1) Inspector (vision — passes image to vLLM)
    inspector = await _run_agent(
        "inspector",
        INSPECTOR_SYSTEM,
        f"Inspect this image for manufacturing defects.\n{context}",
        image_base64=image_base64,
    )

    # 2) Diagnostician (text only)
    diagnostician = await _run_agent(
        "diagnostician",
        DIAGNOSTICIAN_SYSTEM,
        f"INSPECTOR_REPORT:\n{json.dumps(inspector['parsed'])}\n\n{context}",
    )

    # 3) Action (text only)
    action = await _run_agent(
        "action",
        ACTION_SYSTEM,
        (
            f"INSPECTOR_REPORT:\n{json.dumps(inspector['parsed'])}\n\n"
            f"DIAGNOSTICIAN_REPORT:\n{json.dumps(diagnostician['parsed'])}"
        ),
    )

    # 4) Reporter (text only)
    reporter = await _run_agent(
        "reporter",
        REPORTER_SYSTEM,
        (
            f"INSPECTOR_REPORT:\n{json.dumps(inspector['parsed'])}\n\n"
            f"DIAGNOSTICIAN_REPORT:\n{json.dumps(diagnostician['parsed'])}\n\n"
            f"ACTION_REPORT:\n{json.dumps(action['parsed'])}"
        ),
    )

    model_label = AMD_MODEL_NAME
    return {
        "agents": [
            {"role": "inspector",     "label": "Inspector Agent",     "model": model_label, "output": inspector},
            {"role": "diagnostician", "label": "Diagnostician Agent", "model": model_label, "output": diagnostician},
            {"role": "action",        "label": "Action Agent",        "model": model_label, "output": action},
            {"role": "reporter",      "label": "Reporter Agent",      "model": model_label, "output": reporter},
        ],
    }


async def generate_social_post(milestone_title: str, milestone_body: str) -> Dict[str, str]:
    """Generate X + LinkedIn social post drafts for a build-in-public milestone."""
    result = await _run_agent(
        "social",
        SOCIAL_SYSTEM,
        f"Milestone: {milestone_title}\n\nDetails: {milestone_body}",
    )
    parsed = result["parsed"]
    return {
        "x_post": parsed.get("x_post", result["raw"][:260]),
        "linkedin_post": parsed.get("linkedin_post", result["raw"][:600]),
    }
