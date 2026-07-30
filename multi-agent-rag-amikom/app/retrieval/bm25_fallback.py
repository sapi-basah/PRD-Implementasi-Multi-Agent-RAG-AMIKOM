"""BM25 fallback retriever: digunakan hanya saat E5 tidak tersedia.

Response HARUS memuat retrieval_backend=BM25_FALLBACK dan readiness DEGRADED.
Label: DEVELOPMENT_ONLY.
"""

from typing import Any, List

from app.data import chunk_corpus_store, metadata_store
from app.observability import logger
from app.retrieval.service import QueryEncoder, Retriever
from app.schemas import Evidence

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("rank_bm25 not installed. BM25 fallback unavailable.")


class MockQueryEncoder(QueryEncoder):
    """BM25 tidak memerlukan dense encoder."""

    def encode(self, query: str) -> Any:
        return query

    @property
    def is_available(self) -> bool:
        return True


class BM25Retriever(Retriever):
    """BM25 fallback retriever — DEVELOPMENT_ONLY.

    Hanya digunakan ketika E5 benar-benar tidak tersedia.
    """

    def __init__(self):
        self.encoder = MockQueryEncoder()

    @property
    def backend_name(self) -> str:
        return "BM25_FALLBACK"

    def retrieve(
        self,
        query: str,
        namespace: str,
        k: int = 5,
        historical_only: int = 0,
    ) -> List[Evidence]:
        if not BM25_AVAILABLE:
            logger.error("rank_bm25 not installed, BM25 fallback cannot run.")
            return []

        # Metadata-first filtering
        candidates = metadata_store.filter_records(
            retrieval_namespace=namespace,
            historical_only=historical_only,
        )
        if not candidates:
            return []

        # Build corpus dari candidates
        corpus: list = []
        candidate_docs: list = []
        for cand in candidates:
            chunk = chunk_corpus_store.get_chunk(cand["chunk_id"])
            if chunk:
                text = chunk.get("chunk_text", "")
                corpus.append(text.lower().split())
                candidate_docs.append(cand)

        if not corpus:
            return []

        # BM25 ranking
        bm25 = BM25Okapi(corpus)
        tokenized_query = query.lower().split()
        scores = bm25.get_scores(tokenized_query)

        ranked_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:k]

        results: List[Evidence] = []
        for idx in ranked_indices:
            if scores[idx] > 0:
                cand = candidate_docs[idx]
                chunk = chunk_corpus_store.get_chunk(cand["chunk_id"])
                results.append(
                    Evidence(
                        chunk_id=cand["chunk_id"],
                        source_id=cand.get("source_id", ""),
                        title=cand.get("title", ""),
                        locator=cand.get("locator", ""),
                        retrieval_namespace=cand.get("retrieval_namespace", namespace),
                        lifecycle_status=cand.get("lifecycle_status", "ACTIVE"),
                        freshness_status=cand.get("freshness_status", "CURRENT"),
                        score=float(scores[idx]),
                        chunk_text=chunk.get("chunk_text", "") if chunk else "",
                    )
                )
        return results
