import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Konfigurasi aplikasi Multi-Agent RAG AMIKOM.

    Seluruh nilai dapat di-override melalui environment variable atau .env file.
    """

    # --- Application ---
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # --- Data Paths ---
    DATA_ROOT: str = "./data/immutable"
    FAISS_INDEX_PATH: str = "./data/immutable/vector_db/Vector_Database_RAG_AMIKOM_V1/01_database/faiss.index"
    SQLITE_METADATA_PATH: str = "./data/immutable/vector_db/Vector_Database_RAG_AMIKOM_V1/01_database/metadata.sqlite"
    CHUNK_CORPUS_PATH: str = "./data/immutable/chunk/Chunk_Corpus_RAG_AMIKOM_V1/Chunk_Corpus_RAG_AMIKOM_V1.jsonl"
    CONTROL_REGISTRY_PATH: str = "./data/immutable/chunk/Chunk_Corpus_RAG_AMIKOM_V1/chunk_control.jsonl"
    CONFLICT_REGISTRY_PATH: str = "./data/immutable/chunk/Chunk_Corpus_RAG_AMIKOM_V1/chunk_conflict_verifier.jsonl"
    BLOCKED_REGISTRY_PATH: str = "./data/immutable/chunk/Chunk_Corpus_RAG_AMIKOM_V1/chunk_blocked_verifier.jsonl"

    # --- E5 Model ---
    E5_MODEL_PATH: str = "./models/e5/761b726dd34fb83930e26aab4e9ac3899aa1fa78"

    # --- Retrieval ---
    RETRIEVAL_BACKEND: str = "auto"
    RETRIEVAL_TOP_K: int = 10
    BM25_FALLBACK_ENABLED: bool = True

    # --- LLM ---
    LLM_PROVIDER: str = "mock"
    LLM_MODEL: str = ""
    LLM_API_KEY: str = ""
    LLM_TEMPERATURE: float = 0.0
    ENABLE_EXTRACTIVE_FALLBACK: bool = True

    # Backward compatibility aliases
    @property
    def E5_MODEL_DIR(self) -> str:
        return self.E5_MODEL_PATH

    @property
    def METADATA_DB_PATH(self) -> str:
        return self.SQLITE_METADATA_PATH

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
