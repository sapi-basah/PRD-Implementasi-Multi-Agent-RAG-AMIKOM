"""Base agent interface untuk specialist agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from app.retrieval import shared_retrieval_service
from app.schemas import AgentResult, AgentStatus, Evidence, ResponseMode, SubQueryTask, TemporalMode


class BaseAgent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def allowed_namespaces(self) -> List[str]:
        pass

    def retrieve_evidence(
        self,
        query: str,
        namespaces: List[str] | None = None,
        k: int = 10,
    ) -> List[Evidence]:
        """Retrieval per namespace yang diizinkan dengan deterministic merge."""
        ns_list = namespaces or self.allowed_namespaces
        return shared_retrieval_service.retrieve_multi_namespace(
            query=query,
            namespaces=ns_list,
            k_per_namespace=k,
        )

    @abstractmethod
    def process(self, task: SubQueryTask) -> AgentResult:
        """Process sub-query task dan kembalikan AgentResult typed."""
        pass

    def process_request(self, query: str) -> Dict[str, Any]:
        """Backward compatibility for tests expecting process_request(query)."""
        task = SubQueryTask(
            sub_query=query,
            agent=self.name.lower().replace("agent", "").strip(),
            namespace=self.allowed_namespaces,
            temporal_mode=TemporalMode.CURRENT,
            k=5,
        )
        result = self.process(task)
        return {
            "agent": result.agent,
            "status": result.status.value if hasattr(result.status, "value") else str(result.status),
            "evidence": result.evidence,
            "draft_answer": result.draft_answer,
            "unresolved_flags": result.unresolved_flags,
            "handoff": result.handoff,
            "confidence": result.confidence,
        }

    def _build_draft_answer(self, evidence: List[Evidence]) -> str:
        """Buat draft answer dari evidence (digunakan oleh Evidence Selector V2)."""
        if not evidence:
            return ""
        parts = []
        for ev in evidence[:5]:
            if ev.chunk_text:
                parts.append(ev.chunk_text[:200])
        return " ".join(parts)
