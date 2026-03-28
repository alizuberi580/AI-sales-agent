"""
Agent 8: Outreach Agent
Generates cold email and LinkedIn message for each lead.
"""
import asyncio
from typing import Any, Dict, List
from app.services.llm_service import llm_json

PROMPT_TEMPLATE = """
You are a top-performing B2B sales copywriter.

Write personalized outreach for this prospect.

Company: {company_name}
Contact Role: Decision maker / {industry} leader
Hook: {hook}
Pain Angle: {pain_angle}
Value Angle: {value_angle}
Social Proof: {social_proof}
CTA: {call_to_action}
Sender Product: {product_offering}

Return ONLY valid JSON:
{{
  "company_name": "{company_name}",
  "email": {{
    "subject": "string (compelling, under 60 chars)",
    "body": "string (150-200 words, personalized cold email)"
  }},
  "linkedin": {{
    "message": "string (under 300 chars, LinkedIn connection message)"
  }},
  "whatsapp": {{
    "message": "string (casual, under 200 chars)"
  }}
}}
"""


def _fallback_outreach(company: Dict[str, Any], personalization: Dict[str, Any], icp: Dict[str, Any]) -> Dict[str, Any]:
    name = company.get("company_name", "Company")
    industry = company.get("industry", "your industry")
    hook = personalization.get("hook", f"I came across {name} recently")
    pain = personalization.get("pain_angle", "scaling efficiently")
    value = personalization.get("value_angle", "deliver measurable results")
    proof = personalization.get("social_proof", "helped similar companies achieve 40% efficiency gains")
    cta = personalization.get("call_to_action", "open to a 20-minute call next week?")
    product = icp.get("product_offering", "our AI-powered platform")

    email_body = f"""Hi [First Name],

{hook}

I work with {industry} companies on {pain}. {value}

{proof}

{product} is specifically built for teams like yours — and the results speak for themselves.

{cta}

Best,
[Your Name]
[Company] | [Phone]"""

    return {
        "company_name": name,
        "email": {
            "subject": f"Quick question about {name}'s growth strategy",
            "body": email_body
        },
        "linkedin": {
            "message": f"Hi [Name], I came across {name} and love what you're building in the {industry} space. Would love to connect and share something relevant to your team. 🙌"
        },
        "whatsapp": {
            "message": f"Hi! I saw {name} is doing great work in {industry}. We help similar companies with {pain}. Worth a quick chat? 😊"
        }
    }


async def run(companies: List[Dict[str, Any]], personalization_list: List[Dict[str, Any]], icp: Dict[str, Any]) -> List[Dict[str, Any]]:
    personalization_map = {p.get("company_name", ""): p for p in personalization_list}

    async def outreach_one(company: Dict[str, Any]) -> Dict[str, Any]:
        name = company.get("company_name", "")
        personalization = personalization_map.get(name, {})
        fallback = _fallback_outreach(company, personalization, icp)
        prompt = PROMPT_TEMPLATE.format(
            company_name=name,
            industry=company.get("industry", ""),
            hook=personalization.get("hook", ""),
            pain_angle=personalization.get("pain_angle", ""),
            value_angle=personalization.get("value_angle", ""),
            social_proof=personalization.get("social_proof", ""),
            call_to_action=personalization.get("call_to_action", ""),
            product_offering=icp.get("product_offering", "")
        )
        result = await llm_json(prompt, fallback)
        if not isinstance(result, dict) or "email" not in result:
            return fallback
        return result

    return list(await asyncio.gather(*[outreach_one(c) for c in companies[:10]]))
