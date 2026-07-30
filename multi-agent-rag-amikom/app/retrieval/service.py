"""Shared retrieval service: abstraction layer untuk encoder dan retriever."""

from abc import ABC, abstractmethod
from typing import Any, List

from app.schemas import Evidence


class QueryEncoder(ABC):
    @abstractmethod
    def encode(self, query: str) -> Any:
        pass

    @property
    def is_available(self) -> bool:
        return True


class Retriever(ABC):
    @abstractmethod
    def retrieve(
        self,
        query: str,
        namespace: str,
        k: int = 5,
        historical_only: int = 0,
    ) -> List[Evidence]:
        pass

    @property
    def backend_name(self) -> str:
        return "UNKNOWN"


class SharedRetrievalService:
    """Service utama retrieval yang mendukung per-namespace retrieval dan dedup."""

    def __init__(self, encoder: QueryEncoder, retriever: Retriever):
        self.encoder = encoder
        self.retriever = retriever

    @property
    def backend_name(self) -> str:
        return self.retriever.backend_name

    def retrieve(
        self,
        query: str,
        namespace: str,
        k: int = 5,
        historical_only: int = 0,
    ) -> List[Evidence]:
        return self.retriever.retrieve(query, namespace, k, historical_only)

    def retrieve_multi_namespace(
        self,
        query: str,
        namespaces: List[str],
        k_per_namespace: int = 5,
    ) -> List[Evidence]:
        """Retrieval per namespace dengan deterministic merge dan dedup."""
        all_evidence: List[Evidence] = []
        seen_chunk_ids: set = set()

        for ns in namespaces:
            historical = 1 if ns == "archive_schedule" else 0
            results = self.retrieve(query, ns, k=k_per_namespace, historical_only=historical)
            for ev in results:
                if ev.chunk_id not in seen_chunk_ids:
                    seen_chunk_ids.add(ev.chunk_id)
                    all_evidence.append(ev)

        # Sort by score descending (deterministic)
        all_evidence.sort(key=lambda e: (-e.score, e.chunk_id))
        return all_evidence
