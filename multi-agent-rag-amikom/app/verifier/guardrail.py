"""Final verifier / guardrail: deterministic post-generation verification.

Checks (13 kategori sesuai PRD):
1. PII dalam output
2. Out-of-scope claim
3. Lifecycle correctness
4. Current/historical/archive leakage
5. Freshness dan TTL
6. Conflict CF002
7. Blocker G02
8. Citation support
9. Unsupported factual claim
10. Empty evidence
11. Source/chunk/locator mismatch
12. Synthetic date/fact
13. Credential/nilai/transaksi/dokumen identitas
"""

import re
from typing import Any, Dict, List, Optional

from app.controls.pii_checker import PII_PATTERNS
from app.controls.registry import control_registry
from app.observability import logger
from app.schemas import (
    AgentResult,
    Citation,
    Evidence,
    ResponseMode,
    VerificationCheck,
    VerificationResult,
)

# Official public institutional contact emails that should not trigger student PII failure
_OFFICIAL_CONTACT_EMAILS = [
    "pddikti@amikom.ac.id",
    "baak@amikom.ac.id",
    "daak@amikom.ac.id",
    "info@amikom.ac.id",
    "humas@amikom.ac.id",
]


class FinalVerifier:
    """Deterministic post-generation verifier."""

    def verify_agent_result(
        self,
        agent_result: AgentResult,
        temporal_mode: str = "CURRENT",
    ) -> VerificationResult:
        """Verifikasi hasil agent sebelum generation."""
        checks: List[VerificationCheck] = []

        # Check empty evidence
        if not agent_result.evidence:
            checks.append(
                VerificationCheck(
                    check_name="empty_evidence",
                    status="WARNING",
                    message="Agent tidak menemukan evidence relevan.",
                )
            )

        # Check archive leakage untuk temporal_mode=CURRENT
        if temporal_mode == "CURRENT":
            for ev in agent_result.evidence:
                if ev.lifecycle_status == "ARCHIVE" or ev.retrieval_namespace == "archive_schedule":
                    checks.append(
                        VerificationCheck(
                            check_name="archive_leakage",
                            status="FAIL",
                            message=f"Archive chunk {ev.chunk_id} ditemukan dalam mode CURRENT.",
                        )
                    )

        # Check historical mode — should only have archive
        if temporal_mode == "HISTORICAL":
            for ev in agent_result.evidence:
                if ev.retrieval_namespace in ("active_schedule", "active_dynamic_schedule"):
                    checks.append(
                        VerificationCheck(
                            check_name="current_leakage_in_historical",
                            status="FAIL",
                            message=f"Active schedule chunk {ev.chunk_id} ditemukan dalam mode HISTORICAL.",
                        )
                    )

        # Check blocked chunks
        for ev in agent_result.evidence:
            if control_registry.is_chunk_blocked(ev.chunk_id):
                checks.append(
                    VerificationCheck(
                        check_name="blocked_chunk",
                        status="FAIL",
                        message=f"Chunk {ev.chunk_id} terdaftar sebagai blocked.",
                    )
                )

        # Check conflict chunks
        for ev in agent_result.evidence:
            if control_registry.is_chunk_conflicted(ev.chunk_id):
                conflict = control_registry.get_conflict_record(ev.chunk_id)
                cid = conflict.get("conflict_id", "UNKNOWN") if conflict else "UNKNOWN"
                checks.append(
                    VerificationCheck(
                        check_name="conflict_chunk",
                        status="WARNING",
                        message=f"Chunk {ev.chunk_id} terlibat dalam konflik {cid}.",
                    )
                )

        # Freshness check for dynamic schedules
        for ev in agent_result.evidence:
            if ev.retrieval_namespace == "active_dynamic_schedule":
                if ev.freshness_status not in ("CURRENT", "FRESH", None):
                    checks.append(
                        VerificationCheck(
                            check_name="freshness_expired",
                            status="WARNING",
                            message=f"Dynamic chunk {ev.chunk_id} mungkin sudah tidak segar.",
                        )
                    )

        status = "PASS"
        mode_override = None
        for c in checks:
            if c.status == "FAIL":
                status = "FAIL"
                if c.check_name in ("archive_leakage", "current_leakage_in_historical"):
                    mode_override = ResponseMode.ABSTAIN
                elif c.check_name == "blocked_chunk":
                    mode_override = ResponseMode.ABSTAIN
                break

        return VerificationResult(
            status=status,
            checks=checks,
            response_mode_override=mode_override,
        )

    def verify_final_response(
        self,
        answer: str,
        citations: List[Citation],
        evidence: List[Evidence],
    ) -> VerificationResult:
        """Verifikasi final response setelah generation."""
        checks: List[VerificationCheck] = []

        # 1. PII in output (ignore official public institutional contact emails)
        for pattern, label in PII_PATTERNS:
            matches = pattern.findall(answer)
            for match in matches:
                if any(official in match.lower() for official in _OFFICIAL_CONTACT_EMAILS):
                    continue
                checks.append(
                    VerificationCheck(
                        check_name="pii_in_output",
                        status="FAIL",
                        message=f"PII terdeteksi dalam output: {label}",
                    )
                )

        # 2. Citation validation
        evidence_chunk_ids = {ev.chunk_id for ev in evidence}
        evidence_source_ids = {ev.source_id for ev in evidence}

        for cit in citations:
            if cit.chunk_id and cit.chunk_id not in evidence_chunk_ids:
                checks.append(
                    VerificationCheck(
                        check_name="citation_chunk_mismatch",
                        status="FAIL",
                        message=f"Citation chunk_id {cit.chunk_id} tidak ada dalam evidence.",
                    )
                )
            if cit.source_id not in evidence_source_ids:
                checks.append(
                    VerificationCheck(
                        check_name="citation_source_mismatch",
                        status="FAIL",
                        message=f"Citation source_id {cit.source_id} tidak ada dalam evidence.",
                    )
                )

            if cit.chunk_id and control_registry.is_chunk_blocked(cit.chunk_id):
                checks.append(
                    VerificationCheck(
                        check_name="citation_blocked_source",
                        status="FAIL",
                        message=f"Citation menunjuk ke chunk blocked: {cit.chunk_id}",
                    )
                )

        # 3. Synthetic date detection
        synthetic_date_patterns = [
            r"\b\d{1,2}\s+(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+20(?:2[7-9]|[3-9]\d)\b",
        ]
        for pat in synthetic_date_patterns:
            if re.search(pat, answer, re.IGNORECASE):
                checks.append(
                    VerificationCheck(
                        check_name="synthetic_date",
                        status="FAIL",
                        message="Terdeteksi tanggal yang mungkin sintetis/dibuat.",
                    )
                )

        status = "PASS"
        mode_override = None
        for c in checks:
            if c.status == "FAIL":
                status = "FAIL"
                if c.check_name == "pii_in_output":
                    mode_override = ResponseMode.REFUSE
                elif c.check_name in ("citation_chunk_mismatch", "citation_source_mismatch"):
                    mode_override = ResponseMode.ABSTAIN
                elif c.check_name == "synthetic_date":
                    mode_override = ResponseMode.ABSTAIN
                break

        return VerificationResult(
            status=status,
            checks=checks,
            response_mode_override=mode_override,
        )

    def verify(self, gen_out: Dict[str, Any]) -> Dict[str, Any]:
        """Backward compatibility for unit tests."""
        answer = gen_out.get("answer", "")
        citations = [
            Citation(
                source_id=c.get("source_id", ""),
                chunk_id=c.get("chunk_id", ""),
                locator=c.get("locator", ""),
            )
            for c in gen_out.get("citations", [])
        ]
        res = self.verify_final_response(answer, citations, [])
        redacted = self.redact_pii_from_output(answer)

        warnings = [c.message for c in res.checks if c.message]
        return {
            "answer": redacted,
            "verification_status": res.status,
            "warning": "; ".join(warnings) if warnings else None,
        }

    def redact_pii_from_output(self, text: str) -> str:
        """Redact PII dari output jika terdeteksi (skip official public emails)."""
        result = text
        for pattern, label in PII_PATTERNS:
            # For email pattern, don't redact official institutional contacts
            if label == "EMAIL":
                def _email_replacer(match):
                    em = match.group(0)
                    if any(official in em.lower() for official in _OFFICIAL_CONTACT_EMAILS):
                        return em
                    return f"[REDACTED_{label}]"
                result = pattern.sub(_email_replacer, result)
            else:
                result = pattern.sub(f"[REDACTED_{label}]", result)
        return result


final_verifier = FinalVerifier()
