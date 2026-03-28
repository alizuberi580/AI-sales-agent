# AI Sales Co-Pilot — Multi-Agent GTM System

A fully offline-capable, 10-agent AI pipeline for B2B lead generation, research, and personalized outreach.

---

## Quick Start (Zero Config)

Works out of the box with no API keys. All agents use deterministic fallbacks.

```bash
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**

---

## Optional Upgrades (APIs)

Each integration below is **additive** — the system still works without it.

---

## 1. Ollama (Local LLM — FREE, Recommended)

Makes all 10 agents actually call a real LLM instead of using templates.

### Setup

```bash
# Step 1: Download Ollama
# https://ollama.com/download  (Windows installer)

# Step 2: Pull a model (pick one)
ollama pull llama3.2        # recommended — fast, 2GB
ollama pull mistral         # good quality, 4GB
ollama pull phi3            # very fast, 1.5GB

# Step 3: Start Ollama (runs on port 11434 by default)
ollama serve
```

### Configure model in `.env`

```env
OLLAMA_MODEL=llama3.2
OLLAMA_URL=http://localhost:11434/api/generate
```

The backend auto-detects Ollama. If it's running, it uses it. If not, falls back to templates.

---

## 2. OpenAI Embeddings API (Upgrade RAG Quality)

Replaces TF-IDF with real semantic embeddings for much better RAG retrieval.

### Get API Key

1. Go to **https://platform.openai.com/api-keys**
2. Click **Create new secret key**
3. Copy the key (starts with `sk-...`)

### Add to `.env`

```env
OPENAI_API_KEY=sk-your-key-here
```

### Install

```bash
pip install openai
```

### Update `backend/app/rag/vector_store.py`

Add this to the top of the file:

```python
import os
from openai import OpenAI

_openai_client = None

def get_embedding(text: str) -> list[float]:
    global _openai_client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return []  # falls back to TF-IDF
    if _openai_client is None:
        _openai_client = OpenAI(api_key=api_key)
    response = _openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding
```

**Cost:** ~$0.0001 per 1000 tokens. Running the full pipeline costs less than $0.001.

---

## 3. Pinecone (Persistent Vector Database)

Replaces in-memory RAG with a persistent cloud vector store so leads are remembered across sessions.

### Get API Key

1. Go to **https://app.pinecone.io** → Sign up (free tier: 1 index, 100K vectors)
2. Go to **API Keys** → **Create API Key**
3. Copy your key and environment (e.g. `us-east-1-aws`)

### Add to `.env`

```env
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX=sales-copilot
PINECONE_ENVIRONMENT=us-east-1-aws
```

### Install

```bash
pip install pinecone-client
```

### Create Index (one-time setup)

```python
# Run this once in Python to create the index
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key="your-pinecone-api-key")
pc.create_index(
    name="sales-copilot",
    dimension=1536,       # OpenAI text-embedding-3-small
    metric="cosine",
    spec=ServerlessSpec(cloud="aws", region="us-east-1")
)
```

### Update `backend/app/rag/vector_store.py`

```python
import os
from pinecone import Pinecone

_pc = None
_index = None

def get_pinecone_index():
    global _pc, _index
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        return None
    if _index is None:
        _pc = Pinecone(api_key=api_key)
        _index = _pc.Index(os.getenv("PINECONE_INDEX", "sales-copilot"))
    return _index

def store_documents_pinecone(docs: list):
    index = get_pinecone_index()
    if not index:
        return  # fallback to in-memory
    vectors = []
    for i, doc in enumerate(docs):
        embedding = get_embedding(doc["text"])
        if embedding:
            vectors.append({
                "id": f"doc-{i}",
                "values": embedding,
                "metadata": {"text": doc["text"], **doc.get("metadata", {})}
            })
    if vectors:
        index.upsert(vectors=vectors)

def retrieve_context_pinecone(query: str, top_k: int = 3) -> str:
    index = get_pinecone_index()
    if not index:
        return retrieve_context(query, top_k)  # fallback
    q_embedding = get_embedding(query)
    if not q_embedding:
        return retrieve_context(query, top_k)
    results = index.query(vector=q_embedding, top_k=top_k, include_metadata=True)
    if not results.matches:
        return "No relevant context found."
    return "\n\n".join(
        f"[Score: {m.score:.3f}]\n{m.metadata.get('text', '')}"
        for m in results.matches
    )
```

---

## 4. Gmail API (Send Emails Directly from the Dashboard)

Lets you send the generated cold emails directly from the UI.

### Setup (takes ~10 minutes)

**Step 1: Create a Google Cloud Project**

1. Go to **https://console.cloud.google.com**
2. Click **Select a project** → **New Project**
3. Name it `ai-sales-copilot` → **Create**

**Step 2: Enable Gmail API**

1. Go to **APIs & Services** → **Enable APIs and Services**
2. Search for **Gmail API** → **Enable**

**Step 3: Create OAuth Credentials**

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth Client ID**
3. Application type: **Desktop App**
4. Name: `sales-copilot` → **Create**
5. Download the JSON → save as `backend/credentials.json`

**Step 4: Set OAuth Consent Screen**

1. Go to **OAuth Consent Screen**
2. User type: **External**
3. Fill in App name, support email
4. Add scope: `https://www.googleapis.com/auth/gmail.send`
5. Add your email as a **Test user**

### Install

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### Add to `.env`

```env
GMAIL_SENDER=your-email@gmail.com
```

### Create `backend/app/services/gmail_service.py`

```python
import os
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CREDS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def send_email(to: str, subject: str, body: str, sender: str = None) -> dict:
    """Send an email via Gmail API."""
    sender = sender or os.getenv("GMAIL_SENDER", "me")
    service = get_gmail_service()
    message = MIMEText(body)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    result = service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()
    return {"message_id": result["id"], "status": "sent"}
```

### Authorize (run once)

```bash
cd backend
python -c "from app.services.gmail_service import get_gmail_service; get_gmail_service(); print('Authorized!')"
```

A browser window opens → sign in → grant permission → done. Token saved to `token.json`.

### Add send endpoint to `backend/app/routes/pipeline.py`

```python
from app.services.gmail_service import send_email

class SendEmailInput(BaseModel):
    to: str
    subject: str
    body: str

@router.post("/send-email")
async def send_outreach_email(data: SendEmailInput):
    result = send_email(to=data.to, subject=data.subject, body=data.body)
    return {"status": "ok", "data": result}
```

---

## 5. `.env` File (All Keys Together)

Create `backend/.env`:

```env
# LLM (local — no cost)
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.2

# OpenAI (optional — better embeddings)
OPENAI_API_KEY=sk-your-openai-key

# Pinecone (optional — persistent vector store)
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX=sales-copilot
PINECONE_ENVIRONMENT=us-east-1-aws

# Gmail (optional — send emails)
GMAIL_SENDER=your-email@gmail.com
```

Load in `backend/app/main.py` (already configured):

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 6. Full Requirements (with all optional upgrades)

```txt
# Core (required)
fastapi==0.111.0
uvicorn[standard]==0.29.0
httpx==0.27.0
beautifulsoup4==4.12.3
pydantic==2.7.1
python-dotenv==1.0.1

# OpenAI embeddings (optional)
openai>=1.30.0

# Pinecone (optional)
pinecone-client>=3.0.0

# Gmail API (optional)
google-auth>=2.29.0
google-auth-oauthlib>=1.2.0
google-auth-httplib2>=0.2.0
google-api-python-client>=2.128.0
```

---

## Project Structure

```
aihack/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── icp_formatter.py        # Agent 1
│   │   │   ├── query_generator.py      # Agent 2
│   │   │   ├── lead_generator.py       # Agent 3
│   │   │   ├── extraction_agent.py     # Agent 4
│   │   │   ├── research_agent.py       # Agent 5 (RAG)
│   │   │   ├── signal_detection.py     # Agent 6
│   │   │   ├── personalization.py      # Agent 7
│   │   │   ├── outreach_agent.py       # Agent 8
│   │   │   ├── qa_agent.py             # Agent 9
│   │   │   └── followup_agent.py       # Agent 10
│   │   ├── services/
│   │   │   ├── llm_service.py          # Ollama + fallback
│   │   │   ├── scraping_service.py     # DuckDuckGo scraper
│   │   │   └── gmail_service.py        # Gmail (optional)
│   │   ├── routes/
│   │   │   └── pipeline.py             # All API endpoints
│   │   ├── rag/
│   │   │   └── vector_store.py         # TF-IDF RAG (upgradeable to Pinecone)
│   │   ├── data/
│   │   │   └── companies.json          # 20 fallback companies
│   │   └── main.py
│   ├── credentials.json                # Gmail OAuth (optional)
│   ├── token.json                      # Gmail token (auto-generated)
│   ├── .env                            # All API keys
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ICPBuilder.tsx
│   │   │   ├── PipelineStatus.tsx
│   │   │   ├── LeadsTable.tsx
│   │   │   ├── CompanyDetail.tsx
│   │   │   └── QueryViewer.tsx
│   │   ├── lib/
│   │   │   └── api.ts
│   │   └── App.tsx
│   ├── vite.config.ts
│   └── package.json
├── start_backend.bat
├── start_frontend.bat
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/icp` | Format & validate ICP |
| POST | `/api/queries` | Generate search queries |
| POST | `/api/leads` | Generate + score leads |
| POST | `/api/extract` | Extract companies from raw text |
| POST | `/api/research` | RAG research per company |
| POST | `/api/signals` | Detect buying signals |
| POST | `/api/personalization` | Personalization angles |
| POST | `/api/outreach` | Cold email + LinkedIn + WhatsApp |
| POST | `/api/qa` | QA score + improved email |
| POST | `/api/followup` | 3-touch follow-up sequences |
| POST | `/api/pipeline` | **Full pipeline (all agents)** |
| POST | `/api/send-email` | Send via Gmail (optional) |

Interactive docs: **http://localhost:8002/docs**

---

## Upgrade Path Summary

| Feature | Default | With API |
|---------|---------|----------|
| LLM | Template fallback | Ollama (free local) |
| Embeddings | TF-IDF cosine | OpenAI `text-embedding-3-small` |
| Vector Store | In-memory | Pinecone (persistent) |
| Email Sending | Copy to clipboard | Gmail API (send directly) |
| Lead Sourcing | Fallback dataset | DuckDuckGo scraping + dataset |

---

## Troubleshooting

**Pipeline takes too long**
- Normal without Ollama: ~50s (all fallbacks run concurrently)
- With Ollama llama3.2: ~90-120s (real LLM inference)

**Port already in use**
```bash
# Find and kill the process
netstat -ano | findstr :8002
taskkill /PID <pid> /F
```

**CORS errors in browser**
- Make sure backend is running on port 8002
- Vite proxies `/api/*` to `http://localhost:8002`

**Gmail auth fails**
- Make sure you added your email as a Test User in OAuth Consent Screen
- Delete `token.json` and re-run the auth step
