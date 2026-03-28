"""
Agent 6: Signal Detection Agent
Detects buying signals and sales triggers for each company.
"""
import asyncio
from typing import Any, Dict, List
from app.services.llm_service import llm_json

PROMPT_TEMPLATE = """
You are a B2B sales intelligence analyst specializing in buying signal detection.

Analyze this company and identify sales signals.

Company: {company_name}
Industry: {industry}
Growth Stage: {growth_stage}
Description: {description}
Research: {research_summary}
ICP Pain Points: {pain_points}
Our Product: {product_offering}

Return ONLY valid JSON:
{{
  "company_name": "{company_name}",
  "signals": [
    {{
      "type": "string (funding/hiring/expansion/tech_adoption/pain_point)",
      "signal": "string description",
      "strength": "high/medium/low",
      "relevance": "string explaining why this matters for our product"
    }}
  ],
  "overall_signal_strength": "high/medium/low",
  "recommended_action": "string",
  "timing": "string (e.g. 'Reach out now', 'Wait 30 days')"
}}
"""


def _fallback_signals(company: Dict[str, Any], icp: Dict[str, Any]) -> Dict[str, Any]:
    name = company.get("company_name", "Company")
    stage = company.get("growth_stage", "Series A")
    fit_score = company.get("fit_score", 50)

    strength = "high" if fit_score >= 70 else "medium" if fit_score >= 40 else "low"

    signals = [
        {
            "type": "growth_stage",
            "signal": f"Company is at {stage} — actively investing in new tools",
            "strength": "high",
            "relevance": "Companies at this stage typically have budget and urgent need for scalable solutions"
        },
        {
            "type": "pain_point",
            "signal": f"Likely experiencing {icp.get('pain_points', ['scaling challenges'])[0]}",
            "strength": "medium",
            "relevance": f"Directly addressed by {icp.get('product_offering', 'our solution')}"
        },
        {
            "type": "market_expansion",
            "signal": "Company shows signs of market expansion based on industry trends",
            "strength": "medium",
            "relevance": "Expansion creates need for additional tooling and infrastructure"
        }
    ]

    action = "Schedule discovery call" if fit_score >= 60 else "Add to nurture sequence"
    timing = "Reach out this week" if strength == "high" else "Reach out within 2 weeks"

    return {
        "company_name": name,
        "signals": signals,
        "overall_signal_strength": strength,
        "recommended_action": action,
        "timing": timing
    }


async def run(companies: List[Dict[str, Any]], research_list: List[Dict[str, Any]], icp: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Build research lookup
    research_map = {r.get("company_name", ""): r for r in research_list}

    async def signals_one(company: Dict[str, Any]) -> Dict[str, Any]:
        name = company.get("company_name", "")
        research = research_map.get(name, {})
        fallback = _fallback_signals(company, icp)
        prompt = PROMPT_TEMPLATE.format(
            company_name=name,
            industry=company.get("industry", ""),
            growth_stage=company.get("growth_stage", ""),
            description=company.get("description", ""),
            research_summary=research.get("research_summary", ""),
            pain_points=str(icp.get("pain_points", [])),
            product_offering=icp.get("product_offering", "")
        )
        result = await llm_json(prompt, fallback)
        if not isinstance(result, dict) or "signals" not in result:
            return fallback
        return result

    return list(await asyncio.gather(*[signals_one(c) for c in companies[:10]]))
