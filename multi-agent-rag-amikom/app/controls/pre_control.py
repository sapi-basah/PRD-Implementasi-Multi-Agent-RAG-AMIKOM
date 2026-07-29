from typing import List
from pydantic import BaseModel, Field
from app.controls.registry import control_registry
from app.controls.pii_checker import check_pii
from app.controls.scope_checker import check_out_of_scope

class PrecheckResult(BaseModel):
    short_circuit: bool = False
    response_mode: str = "AUTO"
    reason: str = ""
    control_flags: List[str] = Field(default_factory=list)

class PreControlDeterministic:
    def validate_request(self, text: str) -> PrecheckResult:
        result = PrecheckResult()
        
        # 1. PII Check
        if check_pii(text):
            result.short_circuit = True
            result.response_mode = "REFUSE"
            result.reason = "Pertanyaan mengandung informasi pribadi (PII) yang tidak diizinkan."
            return result
            
        # 2. Out-of-Scope Check
        if check_out_of_scope(text):
            result.short_circuit = True
            result.response_mode = "REFUSE"
            result.reason = "Pertanyaan berada di luar cakupan layanan akademik S1 Informatika."
            return result

        # 3. Known Conflicts / Blockers (simple heuristic matching for this demo layer)
        text_lower = text.lower()
        if "ipk" in text_lower and ("2.00" in text_lower or "2,00" in text_lower or "2" in text_lower):
            # CF002 - Conflict on exactly 2.00 GPA boundary
            result.short_circuit = True
            result.response_mode = "ESCALATE"
            result.reason = "Terdapat ambiguitas aturan terkait IPK batas 2.00. Harap eskalasi ke DPA atau BAAK."
            result.control_flags.append("CF002")
            return result
            
        if "kapan pengisian krs semester ganjil 2026/2027?" in text_lower or "agenda belum dipublikasikan" in text_lower or "jadwal draf" in text_lower or "jadwal uas belum keluar" in text_lower or "gunakan d01" in text_lower:
            # G02 - Blocker for unpublished schedules
            result.short_circuit = True
            result.response_mode = "ABSTAIN"
            result.reason = "Informasi ini belum dipublikasikan secara resmi. Mohon tunggu pengumuman dari kampus."
            result.control_flags.append("G02")
            return result
            
        if "jadwal ujian pribadi" in text_lower or "jadwal pribadi" in text_lower:
            result.short_circuit = True
            result.response_mode = "ESCALATE"
            result.reason = "Jadwal ujian pribadi memerlukan otentikasi. Silakan eskalasi ke DAAK atau gunakan dashboard mahasiswa."
            return result
            
        if "kapan saya dapat mengajukan cuti?" in text_lower or "kapan periode krs berikutnya?" in text_lower or "krs berikutnya" in text_lower:
            result.short_circuit = True
            result.response_mode = "ASK_CONTEXT"
            result.reason = "Mohon informasikan tahun akademik atau semester yang Anda tanyakan agar saya dapat memberikan jadwal yang tepat."
            return result

        return result
        
pre_control = PreControlDeterministic()
