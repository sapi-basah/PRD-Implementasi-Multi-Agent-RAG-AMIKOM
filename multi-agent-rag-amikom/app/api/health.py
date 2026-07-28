import os
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.config import settings

router = APIRouter(prefix="/api/v1", tags=["Health & Readiness"])

@router.get("/health")
def get_health():
    faiss_exists = os.path.exists(settings.FAISS_INDEX_PATH)
    sqlite_exists = os.path.exists(settings.METADATA_DB_PATH)
    
    return {
        "status": "healthy",
        "app_env": settings.APP_ENV,
        "database_checks": {
            "faiss_index_exists": faiss_exists,
            "sqlite_db_exists": sqlite_exists
        }
    }

@router.get("/readiness")
def get_readiness():
    e5_model_exists = os.path.exists(settings.E5_MODEL_DIR)
    faiss_exists = os.path.exists(settings.FAISS_INDEX_PATH)
    sqlite_exists = os.path.exists(settings.METADATA_DB_PATH)

    is_ready_for_production = e5_model_exists and faiss_exists and sqlite_exists
    readiness_status = "PRODUCTION_CANDIDATE" if is_ready_for_production else "DEGRADED"
    retrieval_backend = "E5_FAISS" if e5_model_exists else "BM25_FALLBACK"

    return {
        "system_readiness": readiness_status,
        "retrieval_backend": retrieval_backend,
        "e5_model_status": "PASS" if e5_model_exists else "BLOCKED_MODEL_MISSING",
        "vector_database_status": "PASS" if (faiss_exists and sqlite_exists) else "FAIL",
        "bm25_fallback_enabled": settings.BM25_FALLBACK_ENABLED
    }
