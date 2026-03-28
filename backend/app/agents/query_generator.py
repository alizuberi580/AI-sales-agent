"""
Agent 2: Query Generator
Generates targeted search queries based on the ICP.
"""
from typing import Dict, Any, List
from app.services.llm_service import llm_json

PROMPT_TEMPLATE = """
You are a B2B lead generation expert.

Given this ICP, generate 5 targeted web search queries to find matching companies.

ICP:
{icp}

Rules:
- Queries should find real company lists, directories, or articles
- Mix different query formats (top X companies, list of X startups, etc.)
- Be specific to industry and location

Return ONLY valid JSON:
{{
  "queries": [
    "query 1",
    "query 2",
    "query 3",
    "query 4",
    "query 5"
  ]
}}
"""


def _fallback_queries(icp: Dict[str, Any]) -> Dict[str, List[str]]:
    industry = icp.get("industry", "SaaS")
    location = icp.get("location", "")
    size = icp.get("company_size", "mid-market")
    stage = icp.get("growth_stage", "")

    queries = [
        f"top {industry} companies {location} 2024",
        f"list of {industry} startups {location}",
        f"{stage} {industry} companies {location} funding",
        f"best {industry} software companies {location}",
        f"{industry} {location} company directory",
    ]
    return {"queries": [q.strip() for q in queries]}


async def run(icp: Dict[str, Any]) -> Dict[str, List[str]]:
    fallback = _fallback_queries(icp)
    prompt = PROMPT_TEMPLATE.format(icp=str(icp))
    result = await llm_json(prompt, fallback)
    if not isinstance(result, dict) or "queries" not in result:
        return fallback
    if not result["queries"] or len(result["queries"]) < 3:
        return fallback
    return result
