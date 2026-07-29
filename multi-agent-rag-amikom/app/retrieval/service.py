from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.schemas.evidence import Evidence
from app.data import vector_store, metadata_store, chunk_corpus_store
from app.config import settings
from app.observability import logger

class QueryEncoder(ABC):
    @abstractmethod
    def encode(self, query: str) -> Any:
        pass

class Retriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, namespace: str, k: int = 5, historical_only: int = 0) -> List[Evidence]:
        pass

class SharedRetrievalService:
    def __init__(self, encoder: QueryEncoder, retriever: Retriever):
        self.encoder = encoder
        self.retriever = retriever

    def retrieve(self, query: str, namespace: str, k: int = 5, historical_only: int = 0) -> List[Evidence]:
        return self.retriever.retrieve(query, namespace, k, historical_only)

# We will instantiate the appropriate encoder and retriever in __init__.py or dependency injection
