"""FAISS retriever: metadata-first candidate filtering lalu FAISS ranking."""

from typing import List

from app.data import metadata_store, vector_store, chunk_corpus_store
from app.observability import logger
from app.retrieval.service import QueryEncoder, Retriever
from app.schemas import Evidence


class FAISSRetriever(Retriever):
    """Retriever menggunakan E5 + FAISS dengan metadata-first filtering.

    Alur:
    1. SQLite metadata filter → candidate vector_index
    2. E5 encode query → query vector
    3. FAISS search hanya pada candidate indices → ranked results
    4. Assemble Evidence dari metadata + corpus
    """

    def __init__(self, encoder: QueryEncoder):
        self.encoder = encoder

    @property
    def backend_name(self) -> str:
        return "E5_FAISS"

    def retrieve(
        self,
        query: str,
        namespace: str,
        k: int = 5,
        historical_only: int = 0,
    ) -> List[Evidence]:
        if not vector_store.is_available():
            logger.warning("FAISS store not available for retrieval.")
            return []

        # 1. Encode query
        try:
            query_vector = self.encoder.encode(query)
        except Exception as e:
            logger.error(f"Query encoding failed: {e}")
            return []

        # 2. Metadata-first: filter candidates berdasarkan namespace
        candidates = metadata_store.filter_records(
            retrieval_namespace=namespace,
            historical_only=historical_only,
        )

        if not candidates:
            return []

        candidate_indices = [c["vector_index"] for c in candidates]

        # 3. FAISS search hanya pada candidate indices
        results = vector_store.search(query_vector, candidate_indices, k)

        # 4. Assemble Evidence
        evidence_list: List[Evidence] = []
        cand_map = {c["vector_index"]: c for c in candidates}

        for res in results:
            idx = res["vector_index"]
            score = res["score"]
            cand = cand_map.get(idx)
            if cand:
                chunk = chunk_corpus_store.get_chunk(cand["chunk_id"])
                chunk_text = ""
                if chunk:
                    chunk_text = chunk.get("chunk_text", "")
                elif "chunk_text" in cand:
                    chunk_text = cand["chunk_text"]

                evidence_list.append(
                    Evidence(
                        chunk_id=cand["chunk_id"],
                        source_id=cand.get("source_id", ""),
                        title=cand.get("title", ""),
                        locator=cand.get("locator", ""),
                        retrieval_namespace=cand.get("retrieval_namespace", namespace),
                        lifecycle_status=cand.get("lifecycle_status", "ACTIVE"),
                        freshness_status=cand.get("freshness_status", "CURRENT"),
                        score=score,
                        chunk_text=chunk_text,
                    )
                )

        return evidence_list
