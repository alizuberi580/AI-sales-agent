"""
Agent 7: Personalization Agent
Creates personalized messaging angles for each lead.
"""
import asyncio
from typing import Any, Dict, List
from app.services.llm_service import llm_json

PROMPT_TEMPLATE = """
You are an expert B2B sales personalization specialist.

Create a highly personalized outreach angle for this prospect.

Company: {company_name}
Industry: {industry}
Description: {description}
Key Challenges: {key_challenges}
Buying Signals: {signals}
Our Product: {product_offering}
Our Value Prop: {value_proposition}

Return ONLY valid JSON:
{{
  "company_name": "{company_name}",
  "hook": "1 sentence compelling opener specific to this company",
  "pain_angle": "specific pain point we're addressing for them",
  "value_angle": "specific value/ROI we deliver for their situation",
  "social_proof": "relevant case study or proof point (can be fabricated for demo)",
  "call_to_action": "specific low-friction CTA",
  "personalization_notes": "why this angle works for this specific company"
}}
"""


def _fallback_personalization(company: Dict[str, Any], icp: Dict[str, Any], research: Dict[str, Any], signals: Dict[str, Any]) -> Dict[str, Any]:
    name = company.get("company_name", "Company")
    industry = company.get("industry", "SaaS")
    location = company.get("location", "")
    challenges = research.get("key_challenges", ["scaling operations"])
    pain_point = challenges[0] if challenges else "operational efficiency"
    product = icp.get("product_offering", "our solution")
    value_prop = icp.get("value_proposition", "increase revenue and reduce costs")

    return {
        "company_name": name,
        "hook": f"I came across {name} while researching {industry} leaders in {location} — your approach to the market really stood out.",
        "pain_angle": f"Most {industry} companies at your stage struggle with {pain_point} — it's the #1 bottleneck we hear about.",
        "value_angle": f"{product} helps companies like {name} {value_prop} — typically seeing results within 30-60 days.",
        "social_proof": f"We recently helped a similar {industry} company in {location or 'the region'} reduce operational overhead by 40% in their first quarter.",
        "call_to_action": "Would you be open to a 20-minute call next week to see if there's a fit?",
        "personalization_notes": f"Company is a {industry} player in {location} — angle on {pain_point} will resonate given their growth stage."
    }


async def run(companies: List[Dict[str, Any]], research_list: List[Dict[str, Any]], signals_list: List[Dict[str, Any]], icp: Dict[str, Any]) -> List[Dict[str, Any]]:
    research_map = {r.get("company_name", ""): r for r in research_list}
    signals_map = {s.get("company_name", ""): s for s in signals_list}

    async def persona_one(company: Dict[str, Any]) -> Dict[str, Any]:
        name = company.get("company_name", "")
        research = research_map.get(name, {})
        signals = signals_map.get(name, {})
        fallback = _fallback_personalization(company, icp, research, signals)
        prompt = PROMPT_TEMPLATE.format(
            company_name=name,
            industry=company.get("industry", ""),
            description=company.get("description", ""),
            key_challenges=str(research.get("key_challenges", [])),
            signals=str([s.get("signal", "") for s in signals.get("signals", [])]),
            product_offering=icp.get("product_offering", ""),
            value_proposition=icp.get("value_proposition", "")
        )
        result = await llm_json(prompt, fallback)
        if not isinstance(result, dict) or "hook" not in result:
            return fallback
        return result

    return list(await asyncio.gather(*[persona_one(c) for c in companies[:10]]))
