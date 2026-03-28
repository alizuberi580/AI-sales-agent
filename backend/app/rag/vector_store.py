"""
RAG Vector Store — two modes:
  1. Pinecone (cloud, persistent) — when PINECONE_API_KEY is set in .env
     Embeddings generated locally using sentence-transformers (free, no API key)
  2. TF-IDF in-memory (local fallback) — always works, zero setup

Switch is automatic — no code changes needed.
"""
import os
import math
import re
import uuid
from typing import List, Dict, Any, Optional
from collections import Counter

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX   = os.getenv("PINECONE_INDEX", "sales-copilot")

_pinecone_index  = None   # lazy-loaded
_embedder        = None   # lazy-loaded sentence-transformers model


# ── Local embeddings (sentence-transformers) ──────────────────────────────────

def _get_embedder():
    """Load sentence-transformers model once, cache it."""
    global _embedder
    if _embedder is not None:
        return _embedder
    try:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        return _embedder
    except ImportError:
        return None


def _embed(text: str) -> List[float]:
    """
    Generate a 384-dim embedding using all-MiniLM-L6-v2.
    Returns [] if sentence-transformers is not installed.
    """
    model = _get_embedder()
    if model is None:
        return []
    try:
        vec = model.encode(text[:512], normalize_embeddings=True)
        return vec.tolist()
    except Exception:
        return []


# ── Pinecone helpers ───────────────────────────────────────────────────────────

def _get_pinecone_index():
    """Return a connected Pinecone index, or None if not configured."""
    global _pinecone_index
    if _pinecone_index is not None:
        return _pinecone_index
    if not PINECONE_API_KEY:
        return None
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=PINECONE_API_KEY)
        _pinecone_index = pc.Index(PINECONE_INDEX)
        return _pinecone_index
    except Exception:
        return None


def _store_pinecone(docs: List[Dict[str, Any]]) -> bool:
    """Upsert documents into Pinecone. Returns True if successful."""
    index = _get_pinecone_index()
    if not index:
        return False

    vectors = []
    for doc in docs:
        embedding = _embed(doc["text"])
        if not embedding:
            return False  # sentence-transformers not installed → fall back
        vectors.append({
            "id": str(uuid.uuid4()),
            "values": embedding,
            "metadata": {
                "text": doc["text"][:1000],
                **{k: str(v) for k, v in doc.get("metadata", {}).items()}
            }
        })

    if vectors:
        index.upsert(vectors=vectors)
    return True


def _retrieve_pinecone(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Query Pinecone for nearest neighbours. Returns [] if unavailable."""
    index = _get_pinecone_index()
    if not index:
        return []

    q_embedding = _embed(query)
    if not q_embedding:
        return []

    try:
        results = index.query(vector=q_embedding, top_k=top_k, include_metadata=True)
        return [
            {
                "text": m.metadata.get("text", ""),
                "metadata": m.metadata,
                "score": round(m.score, 4)
            }
            for m in results.matches
        ]
    except Exception:
        return []


# ── TF-IDF fallback ────────────────────────────────────────────────────────────

def _tokenize(text: str) -> List[str]:
    return re.findall(r'\b[a-z][a-z0-9]*\b', text.lower())


def _compute_idf(docs: List[List[str]]) -> Dict[str, float]:
    N = len(docs)
    all_words = set(w for doc in docs for w in doc)
    return {
        word: math.log((N + 1) / (sum(1 for doc in docs if word in doc) + 1)) + 1
        for word in all_words
    }


def _tfidf_vector(tokens: List[str], idf: Dict[str, float]) -> Dict[str, float]:
    count = Counter(tokens)
    total = len(tokens) or 1
    return {w: (freq / total) * idf.get(w, 1.0) for w, freq in count.items()}


def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    common = set(a) & set(b)
    dot = sum(a[w] * b[w] for w in common)
    mag = math.sqrt(sum(v**2 for v in a.values())) * math.sqrt(sum(v**2 for v in b.values()))
    return dot / mag if mag else 0.0


class _TFIDFStore:
    def __init__(self):
        self.docs: List[Dict[str, Any]] = []
        self.tokens: List[List[str]] = []
        self.idf: Dict[str, float] = {}
        self.vecs: List[Dict[str, float]] = []

    def add(self, docs: List[Dict[str, Any]]):
        self.docs.extend(docs)
        new_tokens = [_tokenize(d["text"]) for d in docs]
        self.tokens.extend(new_tokens)
        self.idf = _compute_idf(self.tokens)
        self.vecs = [_tfidf_vector(t, self.idf) for t in self.tokens]

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if not self.docs:
            return []
        q_vec = _tfidf_vector(_tokenize(query), self.idf)
        scored = sorted(
            [(i, _cosine(q_vec, v)) for i, v in enumerate(self.vecs)],
            key=lambda x: x[1], reverse=True
        )
        return [
            {"text": self.docs[i]["text"], "metadata": self.docs[i].get("metadata", {}), "score": round(s, 4)}
            for i, s in scored[:top_k]
        ]


_tfidf_store = _TFIDFStore()


# ── Public API (used by agents) ────────────────────────────────────────────────

def store_documents(docs: List[Dict[str, Any]]):
    """
    Store documents for RAG retrieval.
    Uses Pinecone + sentence-transformers if PINECONE_API_KEY is set, otherwise TF-IDF.
    """
    if PINECONE_API_KEY:
        success = _store_pinecone(docs)
        if success:
            return
    _tfidf_store.add(docs)


def retrieve_context(query: str, top_k: int = 3) -> str:
    """
    Retrieve relevant context for a query.
    Uses Pinecone if available, otherwise TF-IDF.
    """
    results = []

    if PINECONE_API_KEY:
        results = _retrieve_pinecone(query, top_k)

    if not results:
        results = _tfidf_store.retrieve(query, top_k)

    if not results:
        return "No relevant context found."

    return "\n\n".join(
        f"[Source: {r['metadata'].get('company', 'unknown')} | Score: {r['score']}]\n{r['text']}"
        for r in results
    )


def get_rag_backend() -> str:
    """Returns which RAG backend is active."""
    if PINECONE_API_KEY and _get_pinecone_index():
        return "pinecone"
    return "tfidf_memory"
