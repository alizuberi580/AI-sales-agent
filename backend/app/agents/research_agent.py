"""
Agent 5: Research Agent (with RAG)
Generates company research summaries using RAG context.
"""
import asyncio
from typing import Any, Dict, List
from app.services.llm_service import llm_json
from app.rag.vector_store import retrieve_context, store_documents

PROMPT_TEMPLATE = """
You are a B2B sales research analyst.

Research this company based on the provided context and general knowledge.

Company: {company_name}
Description: {description}
Industry: {industry}
Location: {location}

RAG Context:
{rag_context}

Return ONLY valid JSON:
{{
  "company_name": "{company_name}",
  "business_model": "string",
  "target_customers": "string",
  "key_challenges": ["challenge1", "challenge2", "challenge3"],
  "recent_developments": "string",
  "competitive_landscape": "string",
  "buying_triggers": ["trigger1", "trigger2"],
  "research_summary": "2-3 sentence overview"
}}
"""


def _index_leads(leads: List[Dict[str, Any]]):
    """Index all lead data into the RAG vector store."""
    docs = []
    for lead in leads:
        text = f"{lead.get('company_name', '')} is a {lead.get('industry', '')} company in {lead.get('location', '')}. {lead.get('description', '')}"
        docs.append({
            "text": text,
            "metadata": {"company": lead.get("company_name", ""), "source": "lead_data"}
        })
    if docs:
        store_documents(docs)


def _fallback_research(company: Dict[str, Any]) -> Dict[str, Any]:
    name = company.get("company_name", "Company")
    industry = company.get("industry", "SaaS")
    location = company.get("location", "")
    desc = company.get("description", "")

    return {
        "company_name": name,
        "business_model": f"B2B {industry} with subscription-based revenue",
        "target_customers": f"Mid-market to enterprise businesses in {location}",
        "key_challenges": [
            "Scaling customer acquisition efficiently",
            "Retaining clients in a competitive market",
            "Integrating with existing enterprise tech stacks"
        ],
        "recent_developments": f"{name} is actively expanding its product suite and market presence. {desc[:100]}",
        "competitive_landscape": f"Operates in the competitive {industry} space with both local and global competitors",
        "buying_triggers": [
            "Recent funding round or growth milestone",
            "Expanding into new markets or verticals"
        ],
        "research_summary": f"{name} is a {industry} company in {location}. {desc[:150]}"
    }


async def run(companies: List[Dict[str, Any]], icp: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Index company data for RAG
    _index_leads(companies)

    # Also index ICP pain points
    pain_docs = [
        {
            "text": f"Target customers experience: {pain}",
            "metadata": {"source": "icp_pain_points"}
        }
        for pain in icp.get("pain_points", [])
    ]
    if pain_docs:
        store_documents(pain_docs)

    async def research_one(company: Dict[str, Any]) -> Dict[str, Any]:
        name = company.get("company_name", "")
        rag_context = retrieve_context(
            f"{name} {company.get('industry', '')} {company.get('description', '')}",
            top_k=3
        )
        fallback = _fallback_research(company)
        prompt = PROMPT_TEMPLATE.format(
            company_name=name,
            description=company.get("description", ""),
            industry=company.get("industry", ""),
            location=company.get("location", ""),
            rag_context=rag_context
        )
        result = await llm_json(prompt, fallback)
        if not isinstance(result, dict) or "company_name" not in result:
            return fallback
        return result

    return list(await asyncio.gather(*[research_one(c) for c in companies[:10]]))
