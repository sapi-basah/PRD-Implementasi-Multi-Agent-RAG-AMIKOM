from .service import SharedRetrievalService, QueryEncoder, Retriever
from .bm25_fallback import BM25Retriever
from .faiss_retriever import FAISSRetriever
from .e5_encoder import E5QueryEncoder
from app.config import settings

# Initialize retrieval service based on settings
if settings.RETRIEVAL_BACKEND == "auto":
    # Try E5 + FAISS first
    encoder = E5QueryEncoder()
    if encoder.session is not None:
        retriever = FAISSRetriever(encoder)
    else:
        # Fallback to BM25 if E5 fails to load
        retriever = BM25Retriever()
        encoder = retriever.encoder
elif settings.RETRIEVAL_BACKEND == "BM25_FALLBACK":
    retriever = BM25Retriever()
    encoder = retriever.encoder
else:
    encoder = E5QueryEncoder()
    retriever = FAISSRetriever(encoder)

shared_retrieval_service = SharedRetrievalService(encoder, retriever)

__all__ = ["SharedRetrievalService", "shared_retrieval_service", "QueryEncoder", "Retriever"]
