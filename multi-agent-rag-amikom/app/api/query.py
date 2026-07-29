from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.pipeline import pipeline_service

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

class CitationResponse(BaseModel):
    source_id: str
    title: str
    locator: str

class MetadataResponse(BaseModel):
    response_mode: str
    processing_time_ms: int
    control_flags: Optional[List[str]] = None
    warning: Optional[str] = None

class QueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[CitationResponse]
    agent_used: Optional[str] = None
    metadata: MetadataResponse

@router.post("/query", response_model=QueryResponse)
def run_query(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    try:
        result = pipeline_service.process(req.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
