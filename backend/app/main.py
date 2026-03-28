import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()  # load .env before anything else

from app.routes.pipeline import router

app = FastAPI(
    title="AI Sales Co-Pilot — Multi-Agent GTM System",
    description="10-agent AI pipeline for B2B lead generation, research, and outreach",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "AI Sales Co-Pilot",
        "version": "1.0.0",
        "agents": [
            "icp_formatter", "query_generator", "lead_generator",
            "extraction_agent", "research_agent", "signal_detection",
            "personalization", "outreach_agent", "qa_agent", "followup_agent"
        ],
        "endpoints": [
            "POST /api/icp", "POST /api/queries", "POST /api/leads",
            "POST /api/extract", "POST /api/research", "POST /api/signals",
            "POST /api/personalization", "POST /api/outreach", "POST /api/qa",
            "POST /api/followup", "POST /api/pipeline"
        ],
        "status": "operational"
    }


@app.get("/health")
async def health():
    from app.rag.vector_store import get_rag_backend
    from app.services.gmail_service import check_gmail_connected
    from app.services.llm_service import GROQ_API_KEY, GROQ_MODEL

    return {
        "status": "healthy",
        "llm": {
            "provider": "groq" if GROQ_API_KEY else "template_fallback",
            "model": GROQ_MODEL if GROQ_API_KEY else "n/a",
            "key_set": bool(GROQ_API_KEY)
        },
        "rag": {
            "backend": get_rag_backend(),
            "pinecone_configured": bool(os.getenv("PINECONE_API_KEY")),
        },
        "gmail": check_gmail_connected()
    }
