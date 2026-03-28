"""
Agent 9: QA Agent
Reviews outreach emails for quality, compliance, and effectiveness.
"""
import asyncio
from typing import Any, Dict, List
from app.services.llm_service import llm_json

PROMPT_TEMPLATE = """
You are a B2B sales email quality assurance expert.

Review this cold outreach email and provide feedback + an improved version.

Company: {company_name}
Email Subject: {subject}
Email Body:
{email_body}

Check for:
1. Personalization quality (is it generic or specific?)
2. Value clarity (is the value proposition clear?)
3. CTA strength (is it low-friction and specific?)
4. Length (100-200 words ideal)
5. Tone (professional but not robotic)
6. Spam trigger words

Return ONLY valid JSON:
{{
  "company_name": "{company_name}",
  "score": 0-100,
  "issues": ["issue1", "issue2"],
  "strengths": ["strength1", "strength2"],
  "improved_subject": "string",
  "improved_email": "string",
  "qa_notes": "string summary"
}}
"""


def _score_email(subject: str, body: str) -> int:
    score = 60  # base score
    spam_words = ["free", "guaranteed", "act now", "limited time", "click here", "buy now"]
    for word in spam_words:
        if word.lower() in body.lower():
            score -= 5

    if len(body) > 100 and len(body) < 300:
        score += 10
    if "?" in body:
        score += 5  # has a question/CTA
    if "[First Name]" in body or "[Name]" in body:
        score += 5  # has personalization placeholder
    if len(subject) < 60:
        score += 5
    if any(word in body.lower() for word in ["results", "roi", "%", "revenue", "save"]):
        score += 10

    return min(score, 100)


def _fallback_qa(company: Dict[str, Any], outreach: Dict[str, Any]) -> Dict[str, Any]:
    name = company.get("company_name", "Company")
    email = outreach.get("email", {})
    subject = email.get("subject", "")
    body = email.get("body", "")
    score = _score_email(subject, body)

    issues = []
    strengths = []

    if "[First Name]" in body:
        issues.append("Email uses placeholder '[First Name]' — replace with actual contact name before sending")
    else:
        strengths.append("Email is addressed to a specific person")

    if len(body) > 300:
        issues.append("Email is too long — trim to under 200 words for better open/reply rates")
    else:
        strengths.append("Email length is optimal (under 200 words)")

    if "?" in body:
        strengths.append("Email ends with a clear question/CTA")
    else:
        issues.append("Missing a clear question or call-to-action")

    if score >= 70:
        strengths.append("Good overall personalization and value clarity")

    # Improve the email slightly
    improved_body = body.replace(
        "Hi [First Name]",
        "Hi {{first_name}}"
    ).replace(
        "Best,",
        "Looking forward to connecting,\n\nBest,"
    )

    return {
        "company_name": name,
        "score": score,
        "issues": issues if issues else ["Minor: Consider adding a specific data point or metric"],
        "strengths": strengths if strengths else ["Personalized opening", "Clear value proposition"],
        "improved_subject": subject if subject else f"Question about {name}'s growth plans",
        "improved_email": improved_body if improved_body != body else body,
        "qa_notes": f"Email scores {score}/100. {'Ready to send with minor tweaks.' if score >= 70 else 'Needs improvement before sending.'}"
    }


async def run(companies: List[Dict[str, Any]], outreach_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    outreach_map = {o.get("company_name", ""): o for o in outreach_list}

    async def qa_one(company: Dict[str, Any]) -> Dict[str, Any]:
        name = company.get("company_name", "")
        outreach = outreach_map.get(name, {})
        email = outreach.get("email", {})
        fallback = _fallback_qa(company, outreach)
        prompt = PROMPT_TEMPLATE.format(
            company_name=name,
            subject=email.get("subject", ""),
            email_body=email.get("body", "")
        )
        result = await llm_json(prompt, fallback)
        if not isinstance(result, dict) or "score" not in result:
            return fallback
        return result

    return list(await asyncio.gather(*[qa_one(c) for c in companies[:10]]))
