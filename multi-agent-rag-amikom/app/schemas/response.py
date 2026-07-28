from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Citation(BaseModel):
    source_id: str = Field(..., description="Kode sumber dokumen")
    locator: str = Field(..., description="Lokasi dokumen (halaman/bagian)")

class VerificationCheck(BaseModel):
    check_name: str
    status: str
    message: Optional[str] = None

class VerificationResult(BaseModel):
    status: str = Field(..., description="PASS, FAIL, atau ESCALATED")
    checks: List[VerificationCheck] = Field(default_factory=list)

class FinalResponse(BaseModel):
    request_id: str = Field(..., description="ID unik request")
    mode: str = Field(..., description="ANSWER, ASK_CONTEXT, ABSTAIN, ESCALATE, HANDOFF, REFUSE")
    answer: str = Field(..., description="Teks jawaban akhir")
    citations: List[Citation] = Field(default_factory=list, description="Daftar sitasi dokumen")
    freshness_notice: Optional[str] = Field(default=None, description="Peringatan kesegaran data dinamis")
    handoff: Optional[str] = Field(default=None, description="Instruksi handoff ke unit terkait")
    retrieval_backend: str = Field(..., description="E5_FAISS atau BM25_FALLBACK")
    system_readiness: str = Field(..., description="PRODUCTION_CANDIDATE atau DEGRADED")
    verification: VerificationResult = Field(..., description="Hasil verifikasi guardrail")
    latency_ms: float = Field(..., description="Total latensi sistem dalam milidetik")
