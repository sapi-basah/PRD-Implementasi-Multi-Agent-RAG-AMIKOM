"""Query API router (POST /api/v1/query & POST /api/query for backward compatibility)."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.pipeline import pipeline_service

router = APIRouter(tags=["Query"])


class QueryApiRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Pertanyaan mahasiswa AMIKOM")
    session_id: Optional[str] = Field(default="demo-session", description="ID sesi pengguna")
    user_context: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {"cohort": "2025"}, description="Konteks pengguna"
    )
    requested_mode: Optional[str] = Field(default="AUTO", description="Mode operasi: AUTO, CURRENT, HISTORICAL")


@router.post("/api/v1/query")
@router.post("/api/query")
def run_query(req: QueryApiRequest) -> Dict[str, Any]:
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query tidak boleh kosong")

    try:
        result = pipeline_service.process(req.query, session_id=req.session_id or "demo-session")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
