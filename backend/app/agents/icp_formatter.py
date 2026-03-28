"""
Agent 1: ICP Formatter
Validates and normalizes the raw ICP input into a clean structured format.
"""
from typing import Any, Dict
from app.services.llm_service import llm_json

PROMPT_TEMPLATE = """
You are an ICP (Ideal Customer Profile) formatter for a B2B SaaS sales system.

Given this raw ICP input, return a clean, normalized JSON object.

Raw ICP:
{raw_icp}

Return ONLY valid JSON with these exact keys:
{{
  "industry": "string",
  "business_type": "string (B2B/B2C/Both)",
  "location": "string (country or region)",
  "company_size": "string (e.g. 50-200 employees)",
  "revenue_range": "string",
  "growth_stage": "string (Seed/Series A/Series B/etc)",
  "pain_points": ["list", "of", "pain", "points"],
  "tech_stack": ["list", "of", "technologies"],
  "product_offering": "string",
  "value_proposition": "string",
  "summary": "one sentence ICP summary"
}}
"""


def _fallback_format(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic fallback — just clean and return the input."""
    pain_points = raw.get("pain_points", [])
    if isinstance(pain_points, str):
        pain_points = [p.strip() for p in pain_points.split(",")]
    tech_stack = raw.get("tech_stack", [])
    if isinstance(tech_stack, str):
        tech_stack = [t.strip() for t in tech_stack.split(",")]

    industry = raw.get("industry", "SaaS")
    location = raw.get("location", "Global")
    product = raw.get("product_offering", "B2B software solution")

    return {
        "industry": industry,
        "business_type": raw.get("business_type", "B2B"),
        "location": location,
        "company_size": raw.get("company_size", "10-200 employees"),
        "revenue_range": raw.get("revenue_range", "$1M-$10M"),
        "growth_stage": raw.get("growth_stage", "Series A"),
        "pain_points": pain_points if pain_points else ["scaling operations", "manual processes"],
        "tech_stack": tech_stack if tech_stack else ["cloud", "APIs"],
        "product_offering": product,
        "value_proposition": raw.get("value_proposition", f"AI-powered {product} for {industry} companies"),
        "summary": f"Targeting {raw.get('company_size', 'mid-market')} {industry} companies in {location}"
    }


async def run(raw_icp: Dict[str, Any]) -> Dict[str, Any]:
    fallback = _fallback_format(raw_icp)
    prompt = PROMPT_TEMPLATE.format(raw_icp=str(raw_icp))
    result = await llm_json(prompt, fallback)
    if not isinstance(result, dict):
        return fallback
    # Ensure all keys exist
    for key, val in fallback.items():
        if key not in result or not result[key]:
            result[key] = val
    return result
