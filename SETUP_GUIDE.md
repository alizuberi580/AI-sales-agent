# AI Sales Co-Pilot — Complete Setup & Flow Guide

---

## How Everything Works (Full Flow)

```
User fills ICP Form (Frontend)
        │
        ▼
POST /api/pipeline (FastAPI Backend)
        │
        ├─ Agent 1: ICP Formatter
        │   Cleans and normalizes your ICP input into strict JSON
        │
        ├─ Agent 2: Query Generator
        │   Generates 5 targeted search queries based on your ICP
        │   e.g. "top SaaS companies Pakistan 2024"
        │
        ├─ Agent 3: Lead Generator
        │   Tries DuckDuckGo scraping with those queries
        │   If scraping returns < 5 clean results → uses local companies.json (20 companies)
        │   Scores each company against your ICP (fit_score 0–100)
        │
        ├─ Agent 4: Extraction Agent
        │   If raw text is passed → extracts company names + descriptions from it
        │   (Used when scraping raw HTML or pasting a list)
        │
        ├─ Agent 5: Research Agent  ← uses RAG
        │   Indexes all company data into the in-memory vector store (TF-IDF)
        │   Retrieves relevant context for each company
        │   Generates: business model, challenges, buying triggers, summary
        │
        ├─ Agent 6: Signal Detection
        │   Detects buying signals per company
        │   e.g. growth stage, market expansion, pain point match
        │   Returns: signal strength (high/medium/low) + recommended timing
        │
        ├─ Agent 7: Personalization
        │   Creates a unique messaging angle per company
        │   Returns: hook, pain angle, value angle, social proof, CTA
        │
        ├─ Agent 8: Outreach Writer
        │   Uses the personalization angle to write:
        │   - Cold email (subject + body)
        │   - LinkedIn connection message
        │   - WhatsApp message
        │
        ├─ Agent 9: QA Agent
        │   Scores the email (0–100)
        │   Identifies issues + strengths
        │   Rewrites an improved version
        │
        └─ Agent 10: Follow-up Sequencer
            Generates a 3-touch follow-up sequence:
            - Touch 1 (Day 3): Email with new value hook
            - Touch 2 (Day 7): LinkedIn message
            - Touch 3 (Day 14): Break-up email

        ▼
Results returned to Frontend
        │
        ├─ Leads Table (scored list)
        ├─ Company Detail Panel (tabs per company)
        │   Overview / Research / Signals / Outreach / QA / Follow-up
        │
        └─ Send Email Button → Review Modal (human-in-the-loop)
                User edits To / Subject / Body → clicks Confirm & Send
                → POST /api/gmail/send → Gmail API → email delivered
```

---

## LLM Behavior

Every agent calls Groq first. If `GROQ_API_KEY` is not set or the call fails, it uses a deterministic template fallback — so the system **never crashes**.

```
Agent calls LLM
    │
    ├─ GROQ_API_KEY set? → calls Groq API (llama-3.3-70b-versatile) — fast + free
    │
    └─ No key / API error? → uses built-in template fallback (instant, always works)
```

All 10 agents run **concurrently per company** using `asyncio.gather`.
A semaphore limits to 5 concurrent Groq calls to stay within free tier rate limits (30 req/min).

---

## What's Built With (No External Frameworks)

| Component | What We Used |
|-----------|-------------|
| Agent system | Plain Python async functions |
| RAG | Custom TF-IDF cosine similarity (zero dependencies) |
| LLM | Groq API (free) with template fallback |
| Web scraping | httpx + BeautifulSoup (DuckDuckGo HTML) |
| Backend | FastAPI + Uvicorn |
| Frontend | React + Vite + Tailwind CSS |
| Email sending | Gmail OAuth2 API |
| No LangChain | ✅ Not used |
| No paid APIs required | ✅ Works $0 out of the box |

---

## External APIs — What You Need & Why

### 1. Groq API — FREE, Required for AI Responses

**Why:** Powers all 10 agents with real LLM intelligence. Without it the system uses template fallbacks — still functional but not AI-generated.

**What it costs:** $0 — Groq has a generous free tier.

**Free tier limits:**
- 30 requests per minute
- 6,000 tokens per minute
- 500,000 tokens per day

**How to get the API key:**

```
Step 1: Go to https://console.groq.com
Step 2: Sign up with Google or email (free)
Step 3: Once logged in, click "API Keys" in the left sidebar
Step 4: Click "Create API Key"
Step 5: Give it a name: sales-copilot
Step 6: Copy the key immediately — it won't be shown again
        It looks like: gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Values to put in .env:**
```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.3-70b-versatile
```

**Available model options:**

| Model | Speed | Quality | Best For |
|-------|-------|---------|----------|
| `llama-3.3-70b-versatile` | Fast | Best | Recommended default |
| `llama3-8b-8192` | Fastest | Good | If hitting rate limits |
| `mixtral-8x7b-32768` | Medium | Great | Long outputs |
| `gemma2-9b-it` | Fast | Good | Lightweight tasks |

---

### 2. Pinecone — Optional (Persistent Vector Store)

**Why:** By default the RAG vector store is in-memory — it resets every time the backend restarts. Pinecone stores all indexed company data permanently in the cloud.

**What it costs:** Free tier gives you 1 index and 100,000 vectors — more than enough.

**How to get the API key:**

#### Step 1: Create a Pinecone account

```
1. Go to https://app.pinecone.io
2. Click "Sign Up Free"
3. Sign up with Google or create an account with email
4. Verify your email if prompted
5. You'll land on the Pinecone dashboard
```

#### Step 2: Get your API Key

```
1. In the left sidebar, click "API Keys"
2. You'll see a default key already created — or click "Create API Key"
3. Give it a name: sales-copilot
4. Click "Create Key"
5. Copy the key immediately — it looks like:
      xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   (UUID format, 36 characters)
6. Note: the "Environment" shown on this page is NOT needed
   for the new Pinecone SDK — only the key is required
```

#### Step 3: Add to .env

```env
PINECONE_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
PINECONE_INDEX=sales-copilot
PINECONE_ENVIRONMENT=us-east-1-aws
```

> Note: `PINECONE_ENVIRONMENT` is kept for reference but the new SDK doesn't require it.
> The index will be created on AWS us-east-1 (free serverless tier).

#### Step 4: Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### Step 6: Create the index (run once)

We've included a setup script that does everything automatically:

```bash
cd backend
python setup_pinecone.py
```

This script will:
- Connect to your Pinecone account
- Create the `sales-copilot` index with dimension=1536 (matches OpenAI embeddings)
- Wait for it to become ready
- Run a test upsert + query to verify everything works
- Print a success message

Expected output:
```
🔗  Connecting to Pinecone...
   Existing indexes: none

📦  Creating index 'sales-copilot'...
   Dimension: 1536
   Metric:    cosine
   Cloud:     AWS us-east-1 (free tier)
   Index created. Waiting for it to be ready...
   Status: True (attempt 3/20)

🧪  Running verification test...
   OpenAI embedding OK — dimension: 1536
   Pinecone upsert OK
   Pinecone query OK — score: 1.0000
   Test vector cleaned up

✅  Pinecone is ready!
```

#### Step 7: Verify it's active at runtime

Once the backend is running, call the health endpoint:

```bash
curl http://localhost:8002/health
```

You should see:
```json
{
  "rag": {
    "backend": "pinecone",
    "pinecone_configured": true,
    "openai_configured": true
  }
}
```

If `"backend": "tfidf_memory"` — Pinecone keys are missing or the connection failed. Check your `.env`.

#### How Pinecone vs TF-IDF differs

| | TF-IDF (default) | Pinecone |
|---|---|---|
| Storage | In-memory, resets on restart | Cloud, permanent |
| Matching | Keyword overlap | Semantic meaning |
| Setup | Zero | 10 minutes |
| Cost | $0 | $0 (free tier) |
| Quality | Good | Much better |

---

### 4. Gmail API — Optional (Send Emails from Dashboard)

**Why:** Lets you click "Send Email" in the dashboard and deliver the generated cold email directly to the prospect's inbox — with a human review step first.

**What it costs:** $0 — Gmail API is free.

**How to set it up (step by step):**

#### Step 1: Create a Google Cloud Project

```
1. Go to https://console.cloud.google.com
2. At the top, click "Select a project" → "New Project"
3. Project name: ai-sales-copilot
4. Click "Create"
5. Make sure your new project is selected in the top bar
```

#### Step 2: Enable the Gmail API

```
1. In the left sidebar go to: APIs & Services → Library
2. Search for "Gmail API"
3. Click on it → click "Enable"
```

#### Step 3: Configure the OAuth Consent Screen

```
1. Go to: APIs & Services → OAuth consent screen
2. User Type: select "External" → click Create
3. Fill in:
   - App name: AI Sales Copilot
   - User support email: your Gmail address
   - Developer contact email: your Gmail address
4. Click "Save and Continue"
5. On the "Scopes" page → click "Save and Continue" (skip for now)
6. On the "Test users" page:
   - Click "+ Add Users"
   - Enter your Gmail address
   - Click "Save and Continue"
7. Click "Back to Dashboard"
```

#### Step 4: Create OAuth Credentials

```
1. Go to: APIs & Services → Credentials
2. Click "+ Create Credentials" → "OAuth Client ID"
3. Application type: select "Desktop app"
4. Name: sales-copilot-desktop
5. Click "Create"
6. A popup appears → click "Download JSON"
7. Rename the downloaded file to: credentials.json
8. Move it to: backend/credentials.json
```

#### Step 5: Install Gmail Dependencies

```bash
cd backend
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

#### Step 6: Authorize (one-time browser login)

```bash
cd backend
python -c "from app.services.gmail_service import authorize_gmail; authorize_gmail()"
```

A browser window will open automatically.
- Sign in with your Gmail account
- Click "Allow"
- The terminal will show: `{'status': 'authorized', ...}`
- A `token.json` file is saved automatically — this is your access token.

#### Step 7: Add to .env

```env
GMAIL_SENDER=yourname@gmail.com
```

**How the human-in-the-loop flow works:**

```
User clicks "Send Email" button on a lead's Outreach tab
        │
        ▼
Review Modal opens (email is NOT sent yet)
        │
        ├─ Shows Gmail status (green = connected, yellow = not connected)
        ├─ Blue notice: "This email won't be sent until you click Confirm & Send"
        ├─ To field: user enters recipient email
        ├─ Subject: pre-filled from AI — user can edit
        ├─ Body: pre-filled from AI — user can edit
        │
        ▼
User clicks "Confirm & Send"
        │
        ▼
POST /api/gmail/send → Gmail API → Email delivered to inbox
        │
        ▼
Success message shown in modal
```

---

## Complete .env File

Create this file at `backend/.env`:

```env
# ── Groq LLM (FREE — get key at console.groq.com) ──
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=llama-3.3-70b-versatile

# ── Pinecone (optional — persistent vector store) ──
PINECONE_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
PINECONE_INDEX=sales-copilot

# ── Gmail (optional — send emails from dashboard) ──
GMAIL_SENDER=yourname@gmail.com
```

> Copy from `backend/.env.example` as a starting point:
> ```bash
> cp backend/.env.example backend/.env
> ```

---

## Priority Order (What to Set Up First)

| Priority | Integration | Impact | Time to Set Up |
|----------|------------|--------|----------------|
| 1 | **Groq API** | Agents become truly intelligent (real LLM) | 2 minutes |
| 2 | **Gmail API** | Send emails directly from dashboard | 10 minutes |
| 3 | **Pinecone** | Persistent semantic RAG across restarts | 10 minutes |

The system works at 100% without any of these — they are all upgrades.

---

## File Reference

```
backend/
├── .env                    ← your actual API keys (never commit this)
├── .env.example            ← template showing all variables
├── credentials.json        ← Gmail OAuth credentials (download from Google Cloud)
├── token.json              ← Gmail access token (auto-generated after authorization)
└── app/
    ├── agents/             ← all 10 AI agents
    ├── services/
    │   ├── llm_service.py      ← Groq API caller + fallback
    │   ├── scraping_service.py ← DuckDuckGo scraper
    │   └── gmail_service.py    ← Gmail OAuth + send
    ├── rag/
    │   └── vector_store.py     ← TF-IDF in-memory RAG
    ├── data/
    │   └── companies.json      ← 20 fallback companies
    └── routes/
        └── pipeline.py         ← all API endpoints
```

---

## Common Questions

**Q: Does this use LangChain?**
No. Everything is built from scratch — custom agents, custom RAG, custom prompts. No framework dependencies.

**Q: What happens if GROQ_API_KEY is not set?**
Every agent falls back to deterministic template generation. The pipeline completes in ~10 seconds and never crashes.

**Q: Can I use a different LLM?**
Yes. Edit `backend/app/services/llm_service.py` — replace `_sync_groq_call()` with any API call (Together AI, Anthropic, etc.).

**Q: Is there any data stored externally by default?**
No. All data is in-memory or in local files. Nothing is sent to any external service unless you configure Groq, Pinecone, or Gmail.

**Q: What if Gmail authorization fails?**
Delete `backend/token.json` and re-run the authorization step. Make sure your Gmail is added as a Test User in the OAuth consent screen.

**Q: The pipeline takes 50+ seconds — is that normal?**
Without a Groq key: ~10 seconds (pure template fallbacks, instant).
With Groq: ~30–60 seconds depending on model and rate limits.
