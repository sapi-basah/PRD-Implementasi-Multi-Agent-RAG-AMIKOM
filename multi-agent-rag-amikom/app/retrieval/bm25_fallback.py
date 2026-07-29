from typing import List, Any
from rank_bm25 import BM25Okapi
from app.retrieval.service import Retriever, QueryEncoder
from app.schemas.evidence import Evidence
from app.data import metadata_store, chunk_corpus_store
from app.observability import logger

class MockQueryEncoder(QueryEncoder):
    """BM25 does not need a dense encoder, so this is just a passthrough."""
    def encode(self, query: str) -> Any:
        return query

class BM25Retriever(Retriever):
    def __init__(self):
        self.encoder = MockQueryEncoder()

    def retrieve(self, query: str, namespace: str, k: int = 5, historical_only: int = 0) -> List[Evidence]:
        # Filter metadata
        candidates = metadata_store.filter_records(
            retrieval_namespace=namespace,
            historical_only=historical_only
        )
        if not candidates:
            return []

        # Gather texts and IDs
        corpus = []
        candidate_docs = []
        for cand in candidates:
            chunk = chunk_corpus_store.get_chunk(cand["chunk_id"])
            if chunk:
                text = chunk.get("chunk_text", "")
                corpus.append(text.lower().split())
                candidate_docs.append(cand)

        if not corpus:
            return []

        # Run BM25
        bm25 = BM25Okapi(corpus)
        tokenized_query = query.lower().split()
        scores = bm25.get_scores(tokenized_query)
        
        # Sort by score descending
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        
        results = []
        for idx in ranked_indices:
            if scores[idx] > 0:  # Only add if it actually matched something
                cand = candidate_docs[idx]
                chunk = chunk_corpus_store.get_chunk(cand["chunk_id"])
                results.append(Evidence(
                    chunk_id=cand["chunk_id"],
                    source_id=cand["source_id"],
                    title=cand["title"],
                    locator=cand["locator"],
                    lifecycle=cand["lifecycle_status"],
                    score=float(scores[idx]),
                    chunk_text=chunk.get("chunk_text", ""),
                    freshness_status=cand.get("freshness_status", "CURRENT")
                ))
        return results
