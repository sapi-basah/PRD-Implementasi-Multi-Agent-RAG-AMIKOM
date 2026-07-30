"""Sources API router (GET /api/v1/sources/{source_id})."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.data import chunk_corpus_store, metadata_store

router = APIRouter(prefix="/api/v1", tags=["Sources"])


@router.get("/sources/{source_id}")
def get_source(source_id: str) -> Dict[str, Any]:
    records = metadata_store.get_records_by_source_id(source_id)
    chunks = chunk_corpus_store.get_chunks_by_source(source_id)

    if not records and not chunks:
        raise HTTPException(
            status_code=404, detail=f"Source ID '{source_id}' tidak ditemukan."
        )

    title = records[0]["title"] if records else (chunks[0].get("title", source_id) if chunks else source_id)
    namespace = records[0]["retrieval_namespace"] if records else "unknown"
    lifecycle = records[0]["lifecycle_status"] if records else "ACTIVE"

    return {
        "source_id": source_id,
        "title": title,
        "retrieval_namespace": namespace,
        "lifecycle_status": lifecycle,
        "record_count": len(records),
        "chunk_count": len(chunks),
        "chunks": [
            {
                "chunk_id": c.get("chunk_id"),
                "locator": c.get("locator"),
                "text_snippet": c.get("chunk_text", "")[:150] + "..." if len(c.get("chunk_text", "")) > 150 else c.get("chunk_text", ""),
            }
            for c in chunks
        ],
    }
