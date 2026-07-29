from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.schemas.evidence import Evidence
from app.retrieval import shared_retrieval_service

class BaseAgent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
        
    @property
    @abstractmethod
    def allowed_namespaces(self) -> List[str]:
        pass

    def retrieve_evidence(self, query: str, **kwargs) -> List[Evidence]:
        """Base retrieval logic. Specialized agents can override this."""
        all_evidence = []
        for ns in self.allowed_namespaces:
            # simple retrieval logic
            evidences = shared_retrieval_service.retrieve(query, namespace=ns, k=3, **kwargs)
            all_evidence.extend(evidences)
        # Sort by score descending and take top 5 overall
        all_evidence.sort(key=lambda e: e.score, reverse=True)
        return all_evidence[:5]

    @abstractmethod
    def process_request(self, query: str) -> Dict[str, Any]:
        """Main entrypoint for the agent."""
        pass
