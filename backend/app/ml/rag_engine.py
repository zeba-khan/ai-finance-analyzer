"""
RAG (Retrieval-Augmented Generation) engine.
Embeds transactions → stores in ChromaDB → retrieves context → answers via Groq LLM.
"""
import os
import json
import chromadb  # type: ignore[import]
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer  # type: ignore[import]
from groq import Groq
from app.config import settings # type: ignore[import]

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_store")
COLLECTION_NAME = "transactions"

# Load embedding model lazily
_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder

# ChromaDB persistent client
_chroma_client = chromadb.PersistentClient(
    path=CHROMA_PATH,
    settings=ChromaSettings(anonymized_telemetry=False),
)

_collection = _chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)


def _make_document(tx: dict) -> str:
    """Convert a transaction dict into a natural language string for embedding."""
    return (
        f"Transaction ID {tx['id']}: {tx['description']} "
        f"for ₹{tx['amount']} on {str(tx['date'])[:10]} "  # type: ignore[import]
        f"in category {tx['category']}."
    )


def upsert_transaction(tx: dict) -> None:
    """Embed and upsert a single transaction into ChromaDB."""
    doc = _make_document(tx)
    embedding = get_embedder().encode(doc).tolist()
    _collection.upsert(
        ids=[str(tx["id"])],
        documents=[doc],
        embeddings=[embedding],
        metadatas=[{
            "amount": float(tx["amount"]),
            "category": str(tx["category"]),
            "date": str(tx["date"])[:10],  # type: ignore[import]
        }],
    )


def upsert_many(transactions: list[dict]) -> None:
    """Bulk upsert transactions into ChromaDB."""
    if not transactions:
        return
    docs = [_make_document(tx) for tx in transactions]
    embeddings = get_embedder().encode(docs).tolist()
    _collection.upsert(
        ids=[str(tx["id"]) for tx in transactions],
        documents=docs,
        embeddings=embeddings,
        metadatas=[{
            "amount": float(tx["amount"]),
            "category": str(tx["category"]),
            "date": str(tx["date"])[:10],  # type: ignore[import]
        } for tx in transactions],
    )


def delete_transaction(tx_id: int) -> None:
    """Remove a transaction from ChromaDB."""
    try:
        _collection.delete(ids=[str(tx_id)])
    except Exception:
        pass


def query(user_question: str, n_results: int = 8) -> str:
    """
    RAG pipeline:
    1. Embed the user question
    2. Retrieve top-N relevant transactions from ChromaDB
    3. Build a prompt with context
    4. Call Groq LLM and return the answer
    """
    # Step 1 — retrieve relevant transactions
    count = _collection.count()
    if count == 0:
        return "No transactions found in the database. Please upload or add some transactions first.", 0  # type: ignore[import]

    question_embedding = get_embedder().encode(user_question).tolist()
    results = _collection.query(
        query_embeddings=[question_embedding],
        n_results=min(n_results, count),
    )

    context_docs = results["documents"][0] if results["documents"] else []
    sources_count = len(context_docs)

    context = "\n".join(context_docs) if context_docs else "No relevant transactions found."

    # Step 2 — build prompt
    system_prompt = """You are a personal finance assistant. 
You are given a list of financial transactions as context.
Answer the user's question using ONLY the provided transaction data.
Be concise, specific, and use ₹ for Indian Rupees.
If the data doesn't contain enough information, say so clearly.
Never make up numbers. Format currency values clearly."""

    user_prompt = f"""Context (relevant transactions):
{context}

User question: {user_question}

Answer based only on the transactions above:"""

    # Step 3 — call Groq LLM
    if not settings.groq_api_key:
        # Fallback: answer without LLM using retrieved context
        return f"Based on your transactions:\n\n{context}\n\n(Add GROQ_API_KEY to .env for AI-powered answers)", sources_count  # type: ignore[import]

    try:
        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=512,
            temperature=0.3,
        )
        answer = response.choices[0].message.content.strip()
        return answer, sources_count  # type: ignore[import]
    except Exception as e:
        return f"LLM error: {str(e)}. Check your GROQ_API_KEY.", sources_count  # type: ignore[import]


def get_collection_count() -> int:
    return _collection.count()
