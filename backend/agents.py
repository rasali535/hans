"""
ForgeSight multi-agent quality-control pipeline.
Uses emergentintegrations.LlmChat with the Emergent Universal LLM key.
Each agent gets a fresh LlmChat session (per the playbook guidance).
"""
import os
import json
import uuid
import re
from typing import Optional, List, Dict, Any
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent


EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")

# Model choices — Claude Sonnet 4.5 is vision-capable and strong for reasoning.
VISION_MODEL = ("anthropic", "claude-sonnet-4-5-20250929")
TEXT_MODEL = ("anthropic", "claude-sonnet-4-5-20250929")


INSPECTOR_SYSTEM = """You are the INSPECTOR agent of ForgeSight — a multimodal quality-control copilot
running on AMD Instinct MI300X + ROCm. Your job: analyze the submitted product/assembly-line
image and surface visible defects, anomalies, or violations.

Return ONLY compact JSON with this exact shape (no prose, no code fences):
{
  "verdict": "pass" | "warn" | "fail",
  "confidence": 0.0-1.0,
  "defects": [
    {"type": "short category e.g. surface-scratch", "severity": "low|medium|high", "location": "short spatial description", "description": "one sentence"}
  ],
  "observation": "2-3 sentence plain-english summary of what you see"
}
Be precise. If the image shows no manufacturing artifact at all, still describe what is visible
and mark verdict "warn" with a defect explaining the mismatch."""


DIAGNOSTICIAN_SYSTEM = """You are the DIAGNOSTICIAN agent of ForgeSight. Given the INSPECTOR's
JSON report and user notes, produce a probable root-cause analysis.

Return ONLY compact JSON:
{
  "probable_cause": "one-sentence most likely cause",
  "contributing_factors": ["factor 1", "factor 2", "factor 3"],
  "affected_process_step": "e.g. CNC milling, injection cooling, weld pass 2"
}
Be concrete and industry-literate."""


ACTION_SYSTEM = """You are the ACTION agent of ForgeSight. Given the INSPECTOR and DIAGNOSTICIAN
outputs, draft an actionable work order.

Return ONLY compact JSON:
{
  "priority": "P0|P1|P2|P3",
  "assignee_role": "e.g. line-lead, maintenance-tech, quality-engineer",
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


def _extract_json(raw: str) -> Dict[str, Any]:
    """Best-effort JSON extraction from an LLM response."""
    if not raw:
        return {}
    # Strip code fences
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    # Try direct
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    # Find first {...} block
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return {"_raw": raw}


async def _run_agent(
    name: str,
    system_message: str,
    user_text: str,
    image_base64: Optional[str] = None,
    provider_model: tuple = TEXT_MODEL,
) -> Dict[str, Any]:
    session_id = f"forgesight-{name}-{uuid.uuid4().hex[:8]}"
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=session_id,
        system_message=system_message,
    ).with_model(provider_model[0], provider_model[1])

    if image_base64:
        msg = UserMessage(
            text=user_text,
            file_contents=[ImageContent(image_base64=image_base64)],
        )
    else:
        msg = UserMessage(text=user_text)

    raw = await chat.send_message(msg)
    raw_str = raw if isinstance(raw, str) else str(raw)
    parsed = _extract_json(raw_str)
    return {"raw": raw_str, "parsed": parsed}


async def run_pipeline(
    image_base64: str,
    notes: str = "",
    product_spec: str = "",
) -> Dict[str, Any]:
    """
    Run the 4-agent pipeline sequentially and return the full transcript.
    """
    context = f"Operator notes: {notes or '(none)'}\nProduct spec: {product_spec or '(generic)'}"

    # 1) Inspector (vision)
    inspector = await _run_agent(
        "inspector",
        INSPECTOR_SYSTEM,
        f"Inspect this image for manufacturing defects.\n{context}",
        image_base64=image_base64,
        provider_model=VISION_MODEL,
    )

    # 2) Diagnostician
    diagnostician = await _run_agent(
        "diagnostician",
        DIAGNOSTICIAN_SYSTEM,
        f"INSPECTOR_REPORT:\n{json.dumps(inspector['parsed'])}\n\n{context}",
        provider_model=TEXT_MODEL,
    )

    # 3) Action
    action = await _run_agent(
        "action",
        ACTION_SYSTEM,
        (
            f"INSPECTOR_REPORT:\n{json.dumps(inspector['parsed'])}\n\n"
            f"DIAGNOSTICIAN_REPORT:\n{json.dumps(diagnostician['parsed'])}"
        ),
        provider_model=TEXT_MODEL,
    )

    # 4) Reporter
    reporter = await _run_agent(
        "reporter",
        REPORTER_SYSTEM,
        (
            f"INSPECTOR_REPORT:\n{json.dumps(inspector['parsed'])}\n\n"
            f"DIAGNOSTICIAN_REPORT:\n{json.dumps(diagnostician['parsed'])}\n\n"
            f"ACTION_REPORT:\n{json.dumps(action['parsed'])}"
        ),
        provider_model=TEXT_MODEL,
    )

    return {
        "agents": [
            {"role": "inspector", "label": "Inspector Agent", "model": "Claude Sonnet 4.5 (Vision)", "output": inspector},
            {"role": "diagnostician", "label": "Diagnostician Agent", "model": "Claude Sonnet 4.5", "output": diagnostician},
            {"role": "action", "label": "Action Agent", "model": "Claude Sonnet 4.5", "output": action},
            {"role": "reporter", "label": "Reporter Agent", "model": "Claude Sonnet 4.5", "output": reporter},
        ],
    }


async def generate_social_post(milestone_title: str, milestone_body: str) -> Dict[str, str]:
    """Generate X + LinkedIn social post drafts for a build-in-public milestone."""
    system = """You craft punchy Build-in-Public social posts for a hackathon project named
"ForgeSight" — a multimodal agentic quality-control copilot running on AMD Instinct MI300X + ROCm.
Always include hashtags: #AMDHackathon #ROCm #AIatAMD #lablab and mention @AIatAMD and @lablab.
Return ONLY JSON:
{"x_post": "<=260 chars, punchy, 1-2 emojis ok", "linkedin_post": "<=600 chars, narrative, 3 short paragraphs"}"""
    result = await _run_agent(
        "social",
        system,
        f"Milestone: {milestone_title}\n\nDetails: {milestone_body}",
        provider_model=TEXT_MODEL,
    )
    parsed = result["parsed"]
    return {
        "x_post": parsed.get("x_post", result["raw"][:260]),
        "linkedin_post": parsed.get("linkedin_post", result["raw"][:600]),
    }
