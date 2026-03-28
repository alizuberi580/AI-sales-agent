"""
Agent 10: Follow-up Agent
Generates a multi-touch follow-up sequence for each lead.
"""
import asyncio
from typing import Any, Dict, List
from app.services.llm_service import llm_json

PROMPT_TEMPLATE = """
You are an expert B2B sales follow-up strategist.

Create a 3-touch follow-up sequence for this prospect who hasn't replied to the initial cold email.

Company: {company_name}
Industry: {industry}
Initial Email Subject: {initial_subject}
Pain Angle: {pain_angle}
Value Angle: {value_angle}
Product: {product_offering}

Return ONLY valid JSON:
{{
  "company_name": "{company_name}",
  "sequence": [
    {{
      "touch": 1,
      "day": 3,
      "channel": "email",
      "subject": "string",
      "message": "string (50-100 words, adds new value)",
      "goal": "string"
    }},
    {{
      "touch": 2,
      "day": 7,
      "channel": "linkedin",
      "subject": "string",
      "message": "string (under 300 chars)",
      "goal": "string"
    }},
    {{
      "touch": 3,
      "day": 14,
      "channel": "email",
      "subject": "string",
      "message": "string (break-up email, 30-50 words)",
      "goal": "string"
    }}
  ],
  "total_touches": 3,
  "recommended_pause_after": "14 days if no response"
}}
"""


def _fallback_followup(company: Dict[str, Any], outreach: Dict[str, Any], personalization: Dict[str, Any], icp: Dict[str, Any]) -> Dict[str, Any]:
    name = company.get("company_name", "Company")
    industry = company.get("industry", "your industry")
    product = icp.get("product_offering", "our solution")
    pain = personalization.get("pain_angle", "your growth challenges")
    initial_subject = outreach.get("email", {}).get("subject", "following up")

    return {
        "company_name": name,
        "sequence": [
            {
                "touch": 1,
                "day": 3,
                "channel": "email",
                "subject": f"Re: {initial_subject}",
                "message": f"Hi [Name], just floating my previous email to the top of your inbox. I know things get busy.\n\nI wanted to share one quick insight: {industry} companies using {product} typically see a 35% reduction in manual work within the first 60 days.\n\nWould a 15-min call this week work?",
                "goal": "Re-engage with a new value hook"
            },
            {
                "touch": 2,
                "day": 7,
                "channel": "linkedin",
                "subject": "LinkedIn follow-up",
                "message": f"Hi [Name], sent you an email last week about helping {name} with {pain}. Would love to connect here if that's easier! 🙏",
                "goal": "Multi-channel touch to increase visibility"
            },
            {
                "touch": 3,
                "day": 14,
                "channel": "email",
                "subject": f"Should I close your file, [Name]?",
                "message": f"Hi [Name], I've reached out a couple of times — I don't want to be a bother if this isn't a priority right now.\n\nShould I close your file, or is there a better time to reconnect?\n\nEither way, no hard feelings — just let me know.",
                "goal": "Break-up email to drive a response or clean close"
            }
        ],
        "total_touches": 3,
        "recommended_pause_after": "14 days if no response"
    }


async def run(
    companies: List[Dict[str, Any]],
    outreach_list: List[Dict[str, Any]],
    personalization_list: List[Dict[str, Any]],
    icp: Dict[str, Any]
) -> List[Dict[str, Any]]:
    outreach_map = {o.get("company_name", ""): o for o in outreach_list}
    personalization_map = {p.get("company_name", ""): p for p in personalization_list}

    async def followup_one(company: Dict[str, Any]) -> Dict[str, Any]:
        name = company.get("company_name", "")
        outreach = outreach_map.get(name, {})
        personalization = personalization_map.get(name, {})
        fallback = _fallback_followup(company, outreach, personalization, icp)
        prompt = PROMPT_TEMPLATE.format(
            company_name=name,
            industry=company.get("industry", ""),
            initial_subject=outreach.get("email", {}).get("subject", ""),
            pain_angle=personalization.get("pain_angle", ""),
            value_angle=personalization.get("value_angle", ""),
            product_offering=icp.get("product_offering", "")
        )
        result = await llm_json(prompt, fallback)
        if not isinstance(result, dict) or "sequence" not in result:
            return fallback
        return result

    return list(await asyncio.gather(*[followup_one(c) for c in companies[:10]]))
