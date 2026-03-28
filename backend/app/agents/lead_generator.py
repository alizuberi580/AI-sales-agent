"""
Agent 3: Lead Generator
Orchestrates web scraping + fallback dataset to produce a raw lead list.
"""
import json
import os
from typing import Dict, Any, List
from app.services.scraping_service import scrape_queries

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "companies.json")


def load_fallback() -> List[Dict[str, Any]]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def filter_by_icp(companies: List[Dict[str, Any]], icp: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Score and filter companies based on ICP match."""
    industry_kw = icp.get("industry", "").lower()
    location_kw = icp.get("location", "").lower()

    filtered = []
    for c in companies:
        score = 0
        c_industry = c.get("industry", "").lower()
        c_location = c.get("location", "").lower()

        if industry_kw and industry_kw.split()[0] in c_industry:
            score += 40
        elif industry_kw and any(w in c_industry for w in industry_kw.split()):
            score += 20

        if location_kw and any(w in c_location for w in location_kw.lower().split()):
            score += 30

        size_map = {
            "1-10": 10, "11-50": 30, "51-200": 75, "201-500": 350,
            "501-1000": 750, "1000+": 1500
        }
        icp_size = icp.get("company_size", "")
        c_size = c.get("company_size", "")
        if icp_size and c_size:
            icp_num = next((v for k, v in size_map.items() if k in icp_size), 100)
            c_num = next((v for k, v in size_map.items() if k in c_size), 100)
            if abs(icp_num - c_num) < 100:
                score += 30

        # Industry keyword partial match bonus
        if "saas" in c_industry:
            score += 10

        c_copy = dict(c)
        c_copy["fit_score"] = min(score, 100)
        filtered.append(c_copy)

    filtered.sort(key=lambda x: x["fit_score"], reverse=True)
    return filtered


async def run(queries: List[str], icp: Dict[str, Any]) -> Dict[str, Any]:
    """
    1. Try web scraping
    2. If insufficient results → use fallback dataset
    3. Score and filter by ICP
    """
    scraped = []
    try:
        scraped = await scrape_queries(queries)
    except Exception:
        pass

    # Filter out scraped results that look like article/page titles (not company names)
    article_patterns = ["top ", "best ", "list of", " - ", " | ", "companies in", " 2024", " 2023", "how to"]
    clean_scraped = [
        s for s in scraped
        if not any(p in s.get("company_name", "").lower() for p in article_patterns)
        and len(s.get("company_name", "")) <= 50
    ]

    if len(clean_scraped) >= 5:
        # Enrich scraped with minimal fields for scoring
        leads = []
        for s in clean_scraped:
            leads.append({
                "company_name": s.get("company_name", "Unknown"),
                "description": s.get("description", ""),
                "industry": icp.get("industry", "SaaS"),
                "location": icp.get("location", ""),
                "company_size": "",
                "revenue_range": "",
                "growth_stage": "",
                "tech_stack": [],
                "fit_score": 50
            })
        source = "web_scraping"
    else:
        leads = load_fallback()
        source = "fallback_dataset"

    scored_leads = filter_by_icp(leads, icp)

    return {
        "source": source,
        "total_found": len(scored_leads),
        "leads": scored_leads[:10]
    }
