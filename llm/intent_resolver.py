"""
Intent Resolver — the ONLY place an LLM is used in this system.

Its single job: translate free text ("show me the latest SOP for part 02736321")
into a structured filter dict. It NEVER touches retrieval or generates an answer —
that stays 100% deterministic SQL in query_engine.py. This boundary is what prevents
the system from ever hallucinating a wrong file.

This is a stub with a rule-based fallback so the pipeline is testable without an API key.
Swap `_call_llm` for a real Anthropic/OpenAI call when ready.
"""

import re
import json


RESOLVER_SYSTEM_PROMPT = """You convert a manufacturing document request into structured JSON.
Extract: doc_type (one of MBD, MBOM, NC, SOP), part_no (string or null), revision ("latest" or a specific value).
Respond with ONLY JSON, no other text. Example: {"doc_type": "SOP", "part_no": "02736321", "revision": "latest"}
"""


def resolve_intent(free_text: str, use_llm: bool = False) -> dict:
    """
    Returns {"doc_type": str|None, "part_no": str|None, "revision": str}
    """
    if use_llm:
        return _call_llm(free_text)
    return _rule_based_fallback(free_text)


def _rule_based_fallback(free_text: str) -> dict:
    """Simple keyword-based resolver — good enough to validate the pipeline shape
    before wiring up a real LLM call."""
    text = free_text.lower()

    doc_type = None
    for dt in ("mbd", "mbom", "nc", "sop"):
        if dt in text:
            doc_type = dt.upper()
            break

    part_match = re.search(r"\b(\d{6,8})\b", free_text)
    part_no = part_match.group(1) if part_match else None

    revision = "latest"
    rev_match = re.search(r"rev(?:ision)?\.?\s*([A-Za-z0-9.]+)", text)
    if rev_match:
        revision = rev_match.group(1)

    return {"doc_type": doc_type, "part_no": part_no, "revision": revision}


def _call_llm(free_text: str) -> dict:
    """
    Real implementation placeholder. E.g.:

    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=200,
        system=RESOLVER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": free_text}],
    )
    return json.loads(response.content[0].text)
    """
    raise NotImplementedError("Wire up a real LLM API call here when ready.")
