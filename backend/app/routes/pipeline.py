"""
All API routes — individual agent endpoints + full pipeline.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from app.services.gmail_service import send_email, check_gmail_connected

from app.agents import (
    icp_formatter,
    query_generator,
    lead_generator,
    extraction_agent,
    research_agent,
    signal_detection,
    personalization,
    outreach_agent,
    qa_agent,
    followup_agent,
)

router = APIRouter()


# ─── Pydantic Models ───────────────────────────────────────────────────────────

class ICPInput(BaseModel):
    industry: str = "SaaS"
    business_type: str = "B2B"
    location: str = "Pakistan"
    company_size: str = "51-200"
    revenue_range: str = "$1M-$10M"
    growth_stage: str = "Series A"
    pain_points: Any = ["manual processes", "scaling operations"]
    tech_stack: Any = ["cloud", "APIs"]
    product_offering: str = "AI-powered sales automation platform"
    value_proposition: str = "Help B2B companies 3x their pipeline with AI"


class QueriesInput(BaseModel):
    icp: Dict[str, Any]


class LeadsInput(BaseModel):
    queries: List[str]
    icp: Dict[str, Any]


class ExtractionInput(BaseModel):
    raw_text: str


class ResearchInput(BaseModel):
    companies: List[Dict[str, Any]]
    icp: Dict[str, Any]


class SignalsInput(BaseModel):
    companies: List[Dict[str, Any]]
    research: List[Dict[str, Any]]
    icp: Dict[str, Any]


class PersonalizationInput(BaseModel):
    companies: List[Dict[str, Any]]
    research: List[Dict[str, Any]]
    signals: List[Dict[str, Any]]
    icp: Dict[str, Any]


class OutreachInput(BaseModel):
    companies: List[Dict[str, Any]]
    personalization: List[Dict[str, Any]]
    icp: Dict[str, Any]


class QAInput(BaseModel):
    companies: List[Dict[str, Any]]
    outreach: List[Dict[str, Any]]


class FollowupInput(BaseModel):
    companies: List[Dict[str, Any]]
    outreach: List[Dict[str, Any]]
    personalization: List[Dict[str, Any]]
    icp: Dict[str, Any]


# ─── Individual Agent Routes ───────────────────────────────────────────────────

@router.post("/icp")
async def format_icp(data: ICPInput):
    result = await icp_formatter.run(data.dict())
    return {"status": "ok", "data": result}


@router.post("/queries")
async def generate_queries(data: QueriesInput):
    result = await query_generator.run(data.icp)
    return {"status": "ok", "data": result}


@router.post("/leads")
async def generate_leads(data: LeadsInput):
    result = await lead_generator.run(data.queries, data.icp)
    return {"status": "ok", "data": result}


@router.post("/extract")
async def extract_companies(data: ExtractionInput):
    result = await extraction_agent.run(data.raw_text)
    return {"status": "ok", "data": result}


@router.post("/research")
async def research_companies(data: ResearchInput):
    result = await research_agent.run(data.companies, data.icp)
    return {"status": "ok", "data": result}


@router.post("/signals")
async def detect_signals(data: SignalsInput):
    result = await signal_detection.run(data.companies, data.research, data.icp)
    return {"status": "ok", "data": result}


@router.post("/personalization")
async def personalize(data: PersonalizationInput):
    result = await personalization.run(data.companies, data.research, data.signals, data.icp)
    return {"status": "ok", "data": result}


@router.post("/outreach")
async def generate_outreach(data: OutreachInput):
    result = await outreach_agent.run(data.companies, data.personalization, data.icp)
    return {"status": "ok", "data": result}


@router.post("/qa")
async def qa_review(data: QAInput):
    result = await qa_agent.run(data.companies, data.outreach)
    return {"status": "ok", "data": result}


@router.post("/followup")
async def generate_followup(data: FollowupInput):
    result = await followup_agent.run(data.companies, data.outreach, data.personalization, data.icp)
    return {"status": "ok", "data": result}


# ─── Full Pipeline Route ───────────────────────────────────────────────────────

@router.post("/pipeline")
async def run_full_pipeline(data: ICPInput):
    """
    Runs the complete multi-agent GTM pipeline end-to-end.
    Never fails — every step has fallback.
    """
    steps = {}

    # Step 1: Format ICP
    formatted_icp = await icp_formatter.run(data.dict())
    steps["icp"] = formatted_icp

    # Step 2: Generate queries
    queries_result = await query_generator.run(formatted_icp)
    queries = queries_result.get("queries", [])
    steps["queries"] = queries_result

    # Step 3: Generate leads (web scrape + fallback)
    leads_result = await lead_generator.run(queries, formatted_icp)
    companies = leads_result.get("leads", [])
    steps["leads"] = leads_result

    # Step 4: Research (with RAG)
    research_list = await research_agent.run(companies, formatted_icp)
    steps["research"] = research_list

    # Step 5: Signal detection
    signals_list = await signal_detection.run(companies, research_list, formatted_icp)
    steps["signals"] = signals_list

    # Step 6: Personalization
    personalization_list = await personalization.run(companies, research_list, signals_list, formatted_icp)
    steps["personalization"] = personalization_list

    # Step 7: Outreach generation
    outreach_list = await outreach_agent.run(companies, personalization_list, formatted_icp)
    steps["outreach"] = outreach_list

    # Step 8: QA
    qa_list = await qa_agent.run(companies, outreach_list)
    steps["qa"] = qa_list

    # Step 9: Follow-up sequences
    followup_list = await followup_agent.run(companies, outreach_list, personalization_list, formatted_icp)
    steps["followup"] = followup_list

    # Build final merged result per company
    company_map = {c["company_name"]: c for c in companies}
    research_map = {r.get("company_name", ""): r for r in research_list}
    signals_map = {s.get("company_name", ""): s for s in signals_list}
    persona_map = {p.get("company_name", ""): p for p in personalization_list}
    outreach_map = {o.get("company_name", ""): o for o in outreach_list}
    qa_map = {q.get("company_name", ""): q for q in qa_list}
    followup_map = {f.get("company_name", ""): f for f in followup_list}

    final_leads = []
    for name, company in company_map.items():
        final_leads.append({
            "company": company,
            "research": research_map.get(name, {}),
            "signals": signals_map.get(name, {}),
            "personalization": persona_map.get(name, {}),
            "outreach": outreach_map.get(name, {}),
            "qa": qa_map.get(name, {}),
            "followup": followup_map.get(name, {})
        })

    return {
        "status": "ok",
        "icp": formatted_icp,
        "queries": queries,
        "pipeline_source": leads_result.get("source", "unknown"),
        "total_leads": len(final_leads),
        "leads": final_leads,
        "steps_completed": list(steps.keys())
    }


# ─── Gmail Routes ──────────────────────────────────────────────────────────────

class SendEmailInput(BaseModel):
    to: str
    subject: str
    body: str
    company_name: Optional[str] = None  # for audit trail


@router.get("/gmail/status")
async def gmail_status():
    """Check if Gmail is connected and ready to send."""
    result = check_gmail_connected()
    return {"status": "ok", "data": result}


@router.post("/gmail/send")
async def send_gmail(data: SendEmailInput):
    """
    Human-in-the-loop email send.
    The frontend shows a review modal before calling this endpoint.
    The user edits and confirms — only then is this called.
    """
    if not data.to or "@" not in data.to:
        raise HTTPException(status_code=400, detail="Invalid recipient email address")
    if not data.subject.strip():
        raise HTTPException(status_code=400, detail="Subject cannot be empty")
    if not data.body.strip():
        raise HTTPException(status_code=400, detail="Email body cannot be empty")

    try:
        result = send_email(
            to=data.to,
            subject=data.subject,
            body=data.body
        )
        return {
            "status": "ok",
            "data": {
                **result,
                "to": data.to,
                "subject": data.subject,
                "company_name": data.company_name
            }
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
