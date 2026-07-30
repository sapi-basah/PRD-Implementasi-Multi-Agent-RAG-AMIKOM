"""Citation formatter dan verifier.

Citation contract:
- Setiap citation harus memuat: source_id, chunk_id, locator
- Citation valid hanya jika ketiganya terdapat dalam evidence yang benar-benar dipakai
- Tidak membuat source_id, chunk_id, atau locator baru
"""

from typing import Any, Dict, List

from app.schemas import Citation, Evidence


class CitationVerifier:
    """Verifikasi dan format citations berdasarkan evidence."""

    def build_citations(
        self,
        raw_citations: List[Dict[str, Any]],
        evidence: List[Evidence],
    ) -> List[Citation]:
        """Build validated citations dari raw citations dan evidence.

        Hanya citation yang benar-benar ada dalam evidence yang diterima.
        """
        evidence_lookup = {}
        for ev in evidence:
            evidence_lookup[ev.chunk_id] = ev
            evidence_lookup[ev.source_id] = ev

        validated: List[Citation] = []
        seen: set = set()

        if raw_citations:
            for rc in raw_citations:
                cid = rc.get("chunk_id", "")
                sid = rc.get("source_id", "")

                if cid in evidence_lookup:
                    ev = evidence_lookup[cid]
                    key = (ev.source_id, ev.chunk_id, ev.locator)
                    if key not in seen:
                        seen.add(key)
                        validated.append(
                            Citation(
                                source_id=ev.source_id,
                                chunk_id=ev.chunk_id,
                                locator=ev.locator,
                            )
                        )
                elif sid in evidence_lookup:
                    ev = evidence_lookup[sid]
                    key = (ev.source_id, ev.chunk_id, ev.locator)
                    if key not in seen:
                        seen.add(key)
                        validated.append(
                            Citation(
                                source_id=ev.source_id,
                                chunk_id=ev.chunk_id,
                                locator=ev.locator,
                            )
                        )

        if not validated and evidence:
            for ev in evidence[:5]:
                key = (ev.source_id, ev.chunk_id, ev.locator)
                if key not in seen:
                    seen.add(key)
                    validated.append(
                        Citation(
                            source_id=ev.source_id,
                            chunk_id=ev.chunk_id,
                            locator=ev.locator,
                        )
                    )

        return validated

    def format_citations(
        self,
        response_text: str,
        evidences: List[Evidence],
    ) -> Dict[str, Any]:
        """Backward compatibility for tests."""
        citations = []
        for ev in evidences:
            citations.append(
                {
                    "source_id": ev.source_id,
                    "chunk_id": ev.chunk_id,
                    "title": ev.title,
                    "locator": ev.locator,
                }
            )

        return {
            "answer": response_text,
            "citations": citations,
        }


citation_verifier = CitationVerifier()
citation_formatter = citation_verifier
