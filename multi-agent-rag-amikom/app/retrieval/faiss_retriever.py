from typing import List
from app.retrieval.service import Retriever, QueryEncoder
from app.schemas.evidence import Evidence
from app.data import vector_store, metadata_store, chunk_corpus_store
from app.observability import logger

class FAISSRetriever(Retriever):
    def __init__(self, encoder: QueryEncoder):
        self.encoder = encoder

    def retrieve(self, query: str, namespace: str, k: int = 5, historical_only: int = 0) -> List[Evidence]:
        if not vector_store.is_available():
            logger.warning("FAISS store not available for retrieval.")
            return []

        # 1. Encode query
        try:
            query_vector = self.encoder.encode(query)
        except Exception as e:
            logger.error(f"Query encoding failed: {e}")
            return []

        # 2. Filter metadata to get candidate indices
        candidates = metadata_store.filter_records(
            retrieval_namespace=namespace,
            historical_only=historical_only
        )
        
        if not candidates:
            return []
            
        candidate_indices = [c["vector_index"] for c in candidates]
        
        # 3. FAISS Search
        results = vector_store.search(query_vector, candidate_indices, k)
        
        # 4. Assemble Evidence
        evidence_list = []
        for res in results:
            idx = res["vector_index"]
            score = res["score"]
            # Find the metadata record for this index
            cand = next((c for c in candidates if c["vector_index"] == idx), None)
            if cand:
                chunk = chunk_corpus_store.get_chunk(cand["chunk_id"])
                evidence_list.append(Evidence(
                    chunk_id=cand["chunk_id"],
                    source_id=cand["source_id"],
                    title=cand["title"],
                    locator=cand["locator"],
                    lifecycle=cand["lifecycle_status"],
                    score=score,
                    chunk_text=chunk.get("chunk_text", "") if chunk else cand.get("chunk_text", ""),
                    freshness_status=cand.get("freshness_status", "CURRENT")
                ))
                
        return evidence_list
