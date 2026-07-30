"""Retrieval package initialization: auto-select E5+FAISS atau BM25 fallback."""

from app.config.settings import settings
from app.observability import logger
from app.retrieval.bm25_fallback import BM25Retriever
from app.retrieval.e5_encoder import E5QueryEncoder
from app.retrieval.faiss_retriever import FAISSRetriever
from app.retrieval.service import QueryEncoder, Retriever, SharedRetrievalService

# Initialize retrieval service based on settings
_encoder: QueryEncoder
_retriever: Retriever

if settings.RETRIEVAL_BACKEND == "BM25_FALLBACK":
    _retriever = BM25Retriever()
    _encoder = _retriever.encoder
    logger.info("Retrieval backend: BM25_FALLBACK (forced by config)")
elif settings.RETRIEVAL_BACKEND == "auto":
    _encoder = E5QueryEncoder()
    if _encoder.is_available:
        _retriever = FAISSRetriever(_encoder)
        logger.info("Retrieval backend: E5_FAISS (auto)")
    else:
        _retriever = BM25Retriever()
        _encoder = _retriever.encoder
        logger.warning("E5 not available, falling back to BM25_FALLBACK (DEVELOPMENT_ONLY)")
else:
    _encoder = E5QueryEncoder()
    _retriever = FAISSRetriever(_encoder)
    logger.info(f"Retrieval backend: E5_FAISS (explicit: {settings.RETRIEVAL_BACKEND})")

shared_retrieval_service = SharedRetrievalService(_encoder, _retriever)

__all__ = [
    "SharedRetrievalService",
    "shared_retrieval_service",
    "QueryEncoder",
    "Retriever",
]
