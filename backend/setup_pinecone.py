"""
One-time Pinecone index setup script.

Run this ONCE after adding PINECONE_API_KEY to backend/.env:
    cd backend
    python setup_pinecone.py

Embeddings are generated locally using sentence-transformers (free, no API key).
Index dimension: 384 (all-MiniLM-L6-v2)
"""
import os
import sys
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("ERROR: python-dotenv not installed. Run: pip install python-dotenv")
    sys.exit(1)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX   = os.getenv("PINECONE_INDEX", "sales-copilot")

# ── Pre-flight checks ──────────────────────────────────────────────────────────

if not PINECONE_API_KEY:
    print("\n❌  PINECONE_API_KEY is not set in backend/.env")
    print("    Get your key at: https://app.pinecone.io → API Keys")
    sys.exit(1)

try:
    from pinecone import Pinecone, ServerlessSpec
except ImportError:
    print("\n❌  pinecone-client not installed.")
    print("    Run: pip install pinecone-client")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
    print("📦  Loading embedding model (all-MiniLM-L6-v2)...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    test_vec = embedder.encode("test", normalize_embeddings=True).tolist()
    DIMENSION = len(test_vec)
    print(f"    Model loaded — dimension: {DIMENSION}")
except ImportError:
    print("\n❌  sentence-transformers not installed.")
    print("    Run: pip install sentence-transformers")
    sys.exit(1)

# ── Connect to Pinecone ────────────────────────────────────────────────────────

print(f"\n🔗  Connecting to Pinecone...")
pc = Pinecone(api_key=PINECONE_API_KEY)

existing_indexes = [idx.name for idx in pc.list_indexes()]
print(f"    Existing indexes: {existing_indexes or 'none'}")

# ── Create index if it doesn't exist ──────────────────────────────────────────

if PINECONE_INDEX in existing_indexes:
    print(f"\n✅  Index '{PINECONE_INDEX}' already exists — skipping creation.")
else:
    print(f"\n📦  Creating index '{PINECONE_INDEX}'...")
    print(f"    Dimension: {DIMENSION}  (all-MiniLM-L6-v2)")
    print(f"    Metric:    cosine")
    print(f"    Cloud:     AWS us-east-1 (free tier)")

    pc.create_index(
        name=PINECONE_INDEX,
        dimension=DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    print(f"    Index created. Waiting for it to become ready...")

    for attempt in range(20):
        time.sleep(3)
        status = pc.describe_index(PINECONE_INDEX).status
        ready = status.get("ready", False)
        print(f"    Ready: {ready} (attempt {attempt + 1}/20)")
        if ready:
            break
    else:
        print("\n⚠️   Index is taking longer than expected.")
        print("    Wait a minute and re-run this script.")
        sys.exit(1)

# ── Verification test ──────────────────────────────────────────────────────────

print(f"\n🧪  Running verification test...")

try:
    idx = pc.Index(PINECONE_INDEX)

    test_text = "AI-powered B2B SaaS company in Pakistan"
    vec = embedder.encode(test_text, normalize_embeddings=True).tolist()

    idx.upsert(vectors=[{
        "id": "test-vector-001",
        "values": vec,
        "metadata": {"text": test_text, "source": "setup_test"}
    }])
    print("    Upsert OK")

    time.sleep(1)
    results = idx.query(vector=vec, top_k=1, include_metadata=True)
    if results.matches:
        print(f"    Query OK — score: {results.matches[0].score:.4f}")
    else:
        print("    ⚠️   Query returned no results (index may still be initializing)")

    idx.delete(ids=["test-vector-001"])
    print("    Test vector cleaned up")

except Exception as e:
    print(f"\n❌  Verification failed: {e}")
    sys.exit(1)

# ── Done ───────────────────────────────────────────────────────────────────────

print(f"""
✅  Pinecone is ready!

    Index name : {PINECONE_INDEX}
    Dimension  : {DIMENSION}
    Metric     : cosine
    Embeddings : sentence-transformers/all-MiniLM-L6-v2 (local, free)

    The RAG system will now use Pinecone automatically.
    Verify at runtime:  GET http://localhost:8002/health  →  "rag.backend": "pinecone"
""")
