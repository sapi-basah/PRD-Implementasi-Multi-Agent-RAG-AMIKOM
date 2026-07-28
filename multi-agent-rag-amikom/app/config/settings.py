import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATA_ROOT: str = "./data/immutable"
    FAISS_INDEX_PATH: str = "./data/immutable/vector_db/Vector_Database_RAG_AMIKOM_V1/01_database/faiss.index"
    METADATA_DB_PATH: str = "./data/immutable/vector_db/Vector_Database_RAG_AMIKOM_V1/01_database/metadata.sqlite"
    CHUNK_CORPUS_PATH: str = "./data/immutable/chunk/Chunk_Corpus_RAG_AMIKOM_V1/Chunk_Corpus_RAG_AMIKOM_V1.jsonl"
    CONTROL_REGISTRY_PATH: str = "./data/immutable/chunk/Chunk_Corpus_RAG_AMIKOM_V1/chunk_control.jsonl"
    CONFLICT_REGISTRY_PATH: str = "./data/immutable/chunk/Chunk_Corpus_RAG_AMIKOM_V1/chunk_conflict_verifier.jsonl"
    BLOCKED_REGISTRY_PATH: str = "./data/immutable/chunk/Chunk_Corpus_RAG_AMIKOM_V1/chunk_blocked_verifier.jsonl"

    E5_MODEL_DIR: str = "./models/e5/761b726dd34fb83930e26aab4e9ac3899aa1fa78"
    RETRIEVAL_BACKEND: str = "auto"
    BM25_FALLBACK_ENABLED: bool = True
    LLM_PROVIDER: str = "mock"
    LLM_MODEL: str = "mock-v1"
    LLM_API_KEY: str = ""
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

