"""Typed schemas for Multi-Agent RAG AMIKOM.

Semua data contract sesuai PRD V1.1 Bagian 10.
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────

class IntentType(str, Enum):
    ACADEMIC = "ACADEMIC"
    SCHEDULE = "SCHEDULE"
    ADMINISTRATION = "ADMINISTRATION"


class TemporalMode(str, Enum):
    CURRENT = "CURRENT"
    HISTORICAL = "HISTORICAL"
    MIXED = "MIXED"


class ResponseMode(str, Enum):
    AUTO = "AUTO"
    ANSWER = "ANSWER"
    ASK_CONTEXT = "ASK_CONTEXT"
    ABSTAIN = "ABSTAIN"
    ESCALATE = "ESCALATE"
    HANDOFF = "HANDOFF"
    REFUSE = "REFUSE"
    LIVE_CHECK_OR_ABSTAIN = "LIVE_CHECK_OR_ABSTAIN"
    ERROR = "ERROR"


class AgentStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    ESCALATED = "ESCALATED"
    REFUSED = "REFUSED"
    ABSTAINED = "ABSTAINED"
    ERROR = "ERROR"


# ── Request ────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Pertanyaan mahasiswa AMIKOM")
    session_id: str = Field(default="demo-session", description="ID sesi pengguna")
    user_context: Dict[str, Any] = Field(default_factory=lambda: {"cohort": "2025"}, description="Konteks pengguna")
    requested_mode: str = Field(default="AUTO", description="Mode operasi: AUTO, CURRENT, HISTORICAL")


# ── Routing ────────────────────────────────────────────────────────────

class SubQueryTask(BaseModel):
    """Tugas sub-query hasil decomposition oleh Coordinator."""
    sub_query: str = Field(..., description="Pertanyaan sub-query")
    agent: str = Field(..., description="Agent target: academic, schedule, administration")
    namespace: List[str] = Field(default_factory=list, description="Namespace retrieval yang diizinkan")
    temporal_mode: TemporalMode = Field(default=TemporalMode.CURRENT)
    k: int = Field(default=10, description="Jumlah retrieval per namespace")


class RoutingDecision(BaseModel):
    """Keputusan routing oleh Coordinator."""
    intents: List[IntentType] = Field(default_factory=list, description="Intent yang terdeteksi")
    temporal_mode: TemporalMode = Field(default=TemporalMode.CURRENT)
    agents: List[str] = Field(default_factory=list, description="Agent yang dipilih")
    subqueries: List[SubQueryTask] = Field(default_factory=list, description="Sub-query tasks")
    control_flags: List[str] = Field(default_factory=list, description="Control flags aktif")
    response_mode: ResponseMode = Field(default=ResponseMode.AUTO)


# ── Evidence ───────────────────────────────────────────────────────────

class Evidence(BaseModel):
    chunk_id: str = Field(..., description="ID unik chunk")
    source_id: str = Field(..., description="Kode dokumen sumber")
    title: str = Field(default="", description="Judul dokumen/sub-bab")
    locator: str = Field(..., description="Lokasi dokumen (halaman/bagian)")
    retrieval_namespace: str = Field(default="", description="Namespace retrieval asal")
    lifecycle_status: str = Field(default="ACTIVE", description="Status lifecycle: ACTIVE, ACTIVE_DYNAMIC, ARCHIVE")
    freshness_status: str = Field(default="CURRENT", description="Status kesegaran data")
    score: float = Field(default=0.0, description="Skor kemiripan retrieval")
    chunk_text: str = Field(default="", description="Isi teks chunk")

    # Backward compat
    @property
    def lifecycle(self) -> str:
        return self.lifecycle_status


# ── Agent Result ───────────────────────────────────────────────────────

class AgentResult(BaseModel):
    """Hasil pemrosesan oleh specialist agent."""
    agent: str = Field(..., description="Nama agent")
    status: AgentStatus = Field(default=AgentStatus.SUCCESS)
    draft_answer: str = Field(default="", description="Draft jawaban dari agent")
    evidence: List[Evidence] = Field(default_factory=list, description="Evidence yang ditemukan")
    unresolved_flags: List[str] = Field(default_factory=list, description="Flags yang belum terselesaikan")
    handoff: Optional[str] = Field(default=None, description="Instruksi handoff")
    confidence: float = Field(default=0.0, description="Confidence score")
    response_mode: ResponseMode = Field(default=ResponseMode.AUTO)


# ── Citation ───────────────────────────────────────────────────────────

class Citation(BaseModel):
    source_id: str = Field(..., description="Kode sumber dokumen")
    chunk_id: str = Field(default="", description="ID chunk")
    locator: str = Field(..., description="Lokasi dokumen (halaman/bagian)")


# ── Verification ───────────────────────────────────────────────────────

class VerificationCheck(BaseModel):
    check_name: str
    status: str  # PASS, FAIL, WARNING
    message: Optional[str] = None


class VerificationResult(BaseModel):
    status: str = Field(..., description="PASS, FAIL, atau ESCALATED")
    checks: List[VerificationCheck] = Field(default_factory=list)
    response_mode_override: Optional[ResponseMode] = Field(default=None)


# ── Final Response ─────────────────────────────────────────────────────

class FinalResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mode: str = Field(..., description="Response mode final")
    answer: str = Field(..., description="Teks jawaban akhir")
    citations: List[Citation] = Field(default_factory=list)
    freshness_notice: Optional[str] = Field(default=None)
    handoff: Optional[str] = Field(default=None)
    retrieval_backend: str = Field(default="E5_FAISS")
    generation_backend: str = Field(default="LLM")
    agents_involved: List[str] = Field(default_factory=list)
    intent: List[str] = Field(default_factory=list)
    temporal_mode: str = Field(default="CURRENT")
    verification: VerificationResult = Field(default_factory=lambda: VerificationResult(status="PENDING"))
    latency_ms: float = Field(default=0.0)
    system_readiness: str = Field(default="DEVELOPMENT")


# ── Readiness ──────────────────────────────────────────────────────────

class ReadinessDetail(BaseModel):
    status: bool = False
    details: Dict[str, Any] = Field(default_factory=dict)


class ReadinessResponse(BaseModel):
    development_ready: ReadinessDetail = Field(default_factory=ReadinessDetail)
    implementation_validated: ReadinessDetail = Field(default_factory=ReadinessDetail)
    final_ready: ReadinessDetail = Field(default_factory=ReadinessDetail)
    retrieval_backend: str = Field(default="UNKNOWN")
    e5_model_status: str = Field(default="UNKNOWN")
    bm25_fallback_enabled: bool = Field(default=True)
