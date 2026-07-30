"""Academic Agent: hanya namespace active_academic.

Tanggung jawab:
- Kurikulum 2025, mata kuliah, SKS, konsentrasi, penyetaraan, kelulusan
- Tidak memilih sendiri klaim yang terkena CF002
"""

from app.agents.base import BaseAgent
from app.controls.registry import control_registry
from app.observability import logger
from app.schemas import AgentResult, AgentStatus, ResponseMode, SubQueryTask


class AcademicAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "AcademicAgent"

    @property
    def allowed_namespaces(self) -> list[str]:
        return ["active_academic"]

    def process(self, task: SubQueryTask) -> AgentResult:
        logger.info(f"{self.name} processing: {task.sub_query[:80]}")

        namespaces = task.namespace if task.namespace else self.allowed_namespaces
        evidence = self.retrieve_evidence(task.sub_query, namespaces=namespaces, k=task.k)

        # Filter out conflicted chunks (CF002) — escalate instead
        clean_evidence = []
        conflict_flags = []
        for ev in evidence:
            if control_registry.is_chunk_conflicted(ev.chunk_id):
                conflict = control_registry.get_conflict_record(ev.chunk_id)
                cid = conflict.get("conflict_id", "UNKNOWN") if conflict else "UNKNOWN"
                conflict_flags.append(f"CF:{cid}:{ev.chunk_id}")
                logger.warning(f"Conflict detected on {ev.chunk_id}: {cid}")
            else:
                clean_evidence.append(ev)

        if conflict_flags and not clean_evidence:
            return AgentResult(
                agent=self.name,
                status=AgentStatus.ESCALATED,
                draft_answer="",
                evidence=evidence,
                unresolved_flags=conflict_flags,
                handoff="Eskalasi ke DPA atau BAAK untuk klarifikasi.",
                confidence=0.0,
                response_mode=ResponseMode.ESCALATE,
            )

        draft = self._build_draft_answer(clean_evidence)

        return AgentResult(
            agent=self.name,
            status=AgentStatus.SUCCESS if clean_evidence else AgentStatus.PARTIAL,
            draft_answer=draft,
            evidence=clean_evidence,
            unresolved_flags=conflict_flags,
            confidence=max(ev.score for ev in clean_evidence) if clean_evidence else 0.0,
            response_mode=ResponseMode.ANSWER if clean_evidence else ResponseMode.ABSTAIN,
        )


academic_agent = AcademicAgent()
