from fastapi import APIRouter, Depends, HTTPException  # type: ignore[import]
from sqlalchemy.orm import Session
from app.database import get_db  # type: ignore[import]
from app.schemas import ChatMessage, ChatResponse  # type: ignore[import]
from app.ml.rag_engine import query, get_collection_count  # type: ignore[import]
from app.services.transaction_service import get_all_with_anomalies  # type: ignore[import]
from app.ml.rag_engine import upsert_many

router = APIRouter(prefix="/chat", tags=["Chat / RAG"])


@router.post("/", response_model=ChatResponse)
def chat(message: ChatMessage, db: Session = Depends(get_db)):
    if not message.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Ensure ChromaDB is populated
    if get_collection_count() == 0:
        txs = get_all_with_anomalies(db)
        if txs:
            upsert_many(txs)

    result = query(message.message)
    if isinstance(result, tuple):
        reply, sources = result
    else:
        reply, sources = result, 0

    return ChatResponse(reply=reply, sources_used=sources)


@router.post("/sync-vectors")
def sync_vectors(db: Session = Depends(get_db)):
    """Re-sync all transactions into ChromaDB (use if vectors are out of date)."""
    txs = get_all_with_anomalies(db)
    upsert_many(txs)
    return {"message": f"Synced {len(txs)} transactions to vector store"}
