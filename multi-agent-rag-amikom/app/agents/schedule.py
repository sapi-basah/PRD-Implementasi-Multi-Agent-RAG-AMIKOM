"""Schedule Agent: current, dynamic, dan historical schedules.

Tanggung jawab:
- Wajib mengklasifikasikan temporal mode
- Current: active_schedule + active_dynamic_schedule (TIDAK archive)
- Historical: archive_schedule SAJA
- Dynamic: cek TTL/freshness
- Tidak boleh menebak tanggal yang belum dipublikasikan
"""

from app.agents.base import BaseAgent
from app.observability import logger
from app.schemas import (
    AgentResult,
    AgentStatus,
    Evidence,
    ResponseMode,
    SubQueryTask,
    TemporalMode,
)


# Namespace mapping berdasarkan temporal mode
_NAMESPACE_MAP = {
    TemporalMode.CURRENT: ["active_schedule", "active_dynamic_schedule"],
    TemporalMode.HISTORICAL: ["archive_schedule"],
    TemporalMode.MIXED: ["active_schedule", "active_dynamic_schedule", "archive_schedule"],
}


class ScheduleAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "ScheduleAgent"

    @property
    def allowed_namespaces(self) -> list[str]:
        return ["active_schedule", "active_dynamic_schedule", "archive_schedule"]

    def _determine_namespaces(self, task: SubQueryTask) -> list[str]:
        """Tentukan namespace berdasarkan temporal mode."""
        if task.namespace:
            return task.namespace
        return _NAMESPACE_MAP.get(task.temporal_mode, _NAMESPACE_MAP[TemporalMode.CURRENT])

    def process(self, task: SubQueryTask) -> AgentResult:
        logger.info(f"{self.name} processing (mode={task.temporal_mode.value}): {task.sub_query[:80]}")

        namespaces = self._determine_namespaces(task)
        evidence = self.retrieve_evidence(task.sub_query, namespaces=namespaces, k=task.k)

        # Validate: current mode should not have archive evidence
        if task.temporal_mode == TemporalMode.CURRENT:
            filtered = [
                ev for ev in evidence
                if ev.retrieval_namespace != "archive_schedule"
            ]
            if len(filtered) < len(evidence):
                logger.warning(
                    f"Archive leakage filtered: {len(evidence) - len(filtered)} chunks removed"
                )
            evidence = filtered

        # Validate: historical mode should only have archive
        if task.temporal_mode == TemporalMode.HISTORICAL:
            filtered = [
                ev for ev in evidence
                if ev.retrieval_namespace == "archive_schedule"
            ]
            evidence = filtered

        # Freshness notice for dynamic schedule
        freshness_flags = []
        for ev in evidence:
            if ev.retrieval_namespace == "active_dynamic_schedule":
                if ev.freshness_status not in ("CURRENT", "FRESH", None):
                    freshness_flags.append(f"STALE:{ev.chunk_id}")

        draft = self._build_draft_answer(evidence)

        return AgentResult(
            agent=self.name,
            status=AgentStatus.SUCCESS if evidence else AgentStatus.PARTIAL,
            draft_answer=draft,
            evidence=evidence,
            unresolved_flags=freshness_flags,
            confidence=max(ev.score for ev in evidence) if evidence else 0.0,
            response_mode=ResponseMode.ANSWER if evidence else ResponseMode.ABSTAIN,
        )


schedule_agent = ScheduleAgent()
