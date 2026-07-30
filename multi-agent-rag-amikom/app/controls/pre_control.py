"""Pre-control: deterministic checks sebelum retrieval.

Checks:
1. PII detection
2. Out-of-scope detection
3. G02 blocker (informasi belum dipublikasikan)
4. CF002 conflict (ambiguitas IPK batas)
5. Personal data request
6. Credential/nilai/transaksi/dokumen identitas
"""

from typing import List

from pydantic import BaseModel, Field

from app.controls.pii_checker import check_pii
from app.controls.scope_checker import check_out_of_scope
from app.observability import logger


class PrecheckResult(BaseModel):
    short_circuit: bool = False
    response_mode: str = "ANSWER"
    reason: str = ""
    control_flags: List[str] = Field(default_factory=list)
    handoff: str | None = None


# Keywords untuk deteksi intent kontrol
_BLOCKER_KEYWORDS = [
    "jadwal semester ganjil 2026",
    "agenda belum dipublikasikan",
    "jadwal draf",
    "jadwal uas belum keluar",
    "kapan pengisian krs semester ganjil",
    "kapan pendaftaran wisuda",
    "jadwal uas belum",
    "belum diumumkan",
]

_PERSONAL_DATA_KEYWORDS = [
    "jadwal ujian pribadi",
    "jadwal pribadi",
    "jadwal saya",
    "nilai saya",
    "transkrip saya",
    "ipk saya",
    "status pembayaran",
    "tagihan saya",
    "nim saya",
    "data pribadi saya",
]

_CREDENTIAL_KEYWORDS = [
    "nilai mata kuliah",
    "transkrip",
    "status keuangan",
    "bukti pembayaran",
    "dokumen identitas",
    "ktp saya",
    "password",
    "kata sandi",
    "login saya",
]

_TEMPORAL_UNPUBLISHED_KEYWORDS = [
    "semester depan",
    "tahun depan",
    "2027",
    "2028",
]


class PreControlDeterministic:
    """Deterministic pre-control sebelum retrieval."""

    def validate_request(self, text: str) -> PrecheckResult:
        result = PrecheckResult()
        text_lower = text.lower().strip()

        # 1. PII Check
        if check_pii(text):
            result.short_circuit = True
            result.response_mode = "REFUSE"
            result.reason = (
                "Pertanyaan mengandung informasi pribadi (PII) yang tidak diizinkan. "
                "Harap hapus data pribadi (NIM, email, nomor telepon, dll) dan ajukan kembali."
            )
            result.control_flags.append("PII_DETECTED")
            return result

        # 2. Out-of-Scope Check
        if check_out_of_scope(text):
            result.short_circuit = True
            result.response_mode = "REFUSE"
            result.reason = (
                "Pertanyaan berada di luar cakupan layanan akademik S1 Informatika "
                "AMIKOM Yogyakarta. Sistem ini hanya melayani pertanyaan seputar "
                "kurikulum, jadwal, dan administrasi akademik."
            )
            result.control_flags.append("OUT_OF_SCOPE")
            return result

        # 3. Personal data / credential request
        for kw in _PERSONAL_DATA_KEYWORDS:
            if kw in text_lower:
                result.short_circuit = True
                result.response_mode = "HANDOFF"
                result.reason = (
                    "Informasi personal (nilai, jadwal pribadi, status pembayaran) "
                    "memerlukan otentikasi. Silakan akses dashboard mahasiswa atau "
                    "hubungi BAAK/DAAK."
                )
                result.handoff = "Dashboard Mahasiswa / BAAK / DAAK"
                result.control_flags.append("PERSONAL_DATA")
                return result

        for kw in _CREDENTIAL_KEYWORDS:
            if kw in text_lower:
                result.short_circuit = True
                result.response_mode = "REFUSE"
                result.reason = (
                    "Sistem tidak memproses data identitas, nilai, transaksi, "
                    "atau dokumen personal. Silakan hubungi unit terkait secara langsung."
                )
                result.control_flags.append("CREDENTIAL_REQUEST")
                return result

        # 4. CF002 — Conflict IPK batas 2.00
        if "ipk" in text_lower and any(
            x in text_lower for x in ["2.00", "2,00", "batas", "minimum"]
        ):
            if "kelulusan" in text_lower or "lulus" in text_lower or "syarat" in text_lower:
                result.short_circuit = True
                result.response_mode = "ESCALATE"
                result.reason = (
                    "Terdapat ambiguitas aturan terkait IPK batas 2.00 (CF002). "
                    "Harap eskalasi ke DPA atau BAAK untuk klarifikasi."
                )
                result.control_flags.append("CF002")
                return result

        # 5. G02 — Blocker informasi belum dipublikasikan
        for kw in _BLOCKER_KEYWORDS:
            if kw in text_lower:
                result.short_circuit = True
                result.response_mode = "ABSTAIN"
                result.reason = (
                    "Informasi ini belum dipublikasikan secara resmi oleh kampus. "
                    "Mohon tunggu pengumuman resmi."
                )
                result.control_flags.append("G02")
                return result

        # 6. Temporal unpublished (future semester)
        for kw in _TEMPORAL_UNPUBLISHED_KEYWORDS:
            if kw in text_lower and any(
                w in text_lower for w in ["jadwal", "krs", "ujian", "perkuliahan"]
            ):
                result.short_circuit = True
                result.response_mode = "LIVE_CHECK_OR_ABSTAIN"
                result.reason = (
                    "Jadwal untuk periode yang Anda tanyakan mungkin belum tersedia. "
                    "Silakan cek pengumuman resmi kampus secara berkala."
                )
                result.control_flags.append("TEMPORAL_FUTURE")
                return result

        # 7. Context ambiguity — kapan cuti/krs berikutnya tanpa spesifikasi
        if any(
            phrase in text_lower
            for phrase in [
                "kapan saya dapat mengajukan cuti",
                "kapan periode krs berikutnya",
                "krs berikutnya",
            ]
        ):
            result.short_circuit = True
            result.response_mode = "ASK_CONTEXT"
            result.reason = (
                "Mohon informasikan tahun akademik atau semester yang Anda tanyakan "
                "agar saya dapat memberikan jadwal yang tepat."
            )
            result.control_flags.append("CONTEXT_NEEDED")
            return result

        return result


pre_control = PreControlDeterministic()
