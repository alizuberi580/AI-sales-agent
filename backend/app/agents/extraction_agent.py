"""
Agent 4: Extraction Agent
Extracts structured company data from raw text/HTML snippets.
"""
from typing import Any, Dict, List
from app.services.llm_service import llm_json

PROMPT_TEMPLATE = """
You are a data extraction specialist for B2B lead generation.

Extract structured company information from the following raw text.

Raw text:
{raw_text}

Return ONLY valid JSON array:
[
  {{
    "company_name": "string",
    "description": "string (1-2 sentences)",
    "industry": "string",
    "location": "string",
    "company_size": "string",
    "website": "string or empty"
  }}
]

Extract up to 10 companies. If no companies found, return empty array [].
"""


def _parse_text_fallback(raw_text: str) -> List[Dict[str, Any]]:
    """Simple line-by-line extraction as fallback."""
    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
    companies = []
    for line in lines[:20]:
        if 3 <= len(line) <= 100 and not line.startswith(("http", "#", "-")):
            companies.append({
                "company_name": line,
                "description": "",
                "industry": "",
                "location": "",
                "company_size": "",
                "website": ""
            })
    return companies[:10]


async def run(raw_text: str) -> Dict[str, Any]:
    fallback = _parse_text_fallback(raw_text)
    if not raw_text.strip():
        return {"extracted": [], "count": 0}

    prompt = PROMPT_TEMPLATE.format(raw_text=raw_text[:3000])
    result = await llm_json(prompt, fallback)

    if isinstance(result, list):
        extracted = result
    elif isinstance(result, dict) and "companies" in result:
        extracted = result["companies"]
    else:
        extracted = fallback

    return {"extracted": extracted, "count": len(extracted)}
