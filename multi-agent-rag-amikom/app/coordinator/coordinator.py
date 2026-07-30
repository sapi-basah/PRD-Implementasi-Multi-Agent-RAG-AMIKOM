"""Coordinator: intent classification, temporal mode, decomposition, multi-agent routing, merge.

Coordinator TIDAK memiliki knowledge namespace dan TIDAK menulis fakta.
"""

from typing import Any, Dict, List

from app.agents.academic import academic_agent
from app.agents.admin import admin_agent
from app.agents.schedule import schedule_agent
from app.observability import logger
from app.schemas import (
    AgentResult,
    AgentStatus,
    Evidence,
    IntentType,
    ResponseMode,
    RoutingDecision,
    SubQueryTask,
    TemporalMode,
)

# Agent registry
_AGENTS = {
    "academic": academic_agent,
    "schedule": schedule_agent,
    "administration": admin_agent,
    "admin": admin_agent,
}

_ACADEMIC_KEYWORDS = [
    "kurikulum", "mata kuliah", "sks", "konsentrasi", "penyetaraan",
    "kelulusan", "lulus", "prasyarat", "semester", "jurusan",
    "informatika", "prodi", "studi", "kredit", "akademik",
    "matkul", "mk ", "dosen", "wali", "dpa", "skripsi",
]

_SCHEDULE_KEYWORDS = [
    "jadwal", "tanggal", "ujian", "kalender", "agenda",
    "krs", "perkuliahan", "uas", "uts", "kuliah",
    "libur", "wisuda", "registrasi", "herregistrasi",
    "pengisian krs", "perubahan krs",
]

_ADMIN_KEYWORDS = [
    "cuti", "surat", "administrasi", "legalisir", "ktm",
    "skak", "pddikti", "krs manual", "prosedur", "persyaratan",
    "pengajuan", "dokumen", "formulir", "permohonan",
]

_HISTORICAL_KEYWORDS = [
    "dulu", "lalu", "sebelumnya", "tahun lalu", "semester lalu",
    "kemarin", "lampau", "historis", "arsip", "2024", "2023",
    "yang sudah lewat",
]


class BackwardCompatRoutingDecision:
    def __init__(self, agent_id: str, confidence: float = 0.9, reason: str = ""):
        self.agent_id = agent_id
        self.confidence = confidence
        self.reason = reason


class Coordinator:
    """Multi-intent coordinator dengan decomposition dan merge."""

    def classify_intents(self, query: str) -> List[IntentType]:
        query_lower = query.lower()
        intents = []

        academic_score = sum(1 for kw in _ACADEMIC_KEYWORDS if kw in query_lower)
        schedule_score = sum(1 for kw in _SCHEDULE_KEYWORDS if kw in query_lower)
        admin_score = sum(1 for kw in _ADMIN_KEYWORDS if kw in query_lower)

        if schedule_score > 0:
            intents.append(IntentType.SCHEDULE)
        if admin_score > 0:
            intents.append(IntentType.ADMINISTRATION)
        if academic_score > 0:
            intents.append(IntentType.ACADEMIC)

        if not intents:
            intents.append(IntentType.ACADEMIC)

        return intents

    def classify_temporal_mode(self, query: str) -> TemporalMode:
        query_lower = query.lower()
        is_historical = any(kw in query_lower for kw in _HISTORICAL_KEYWORDS)
        is_current = any(
            kw in query_lower
            for kw in ["sekarang", "saat ini", "terkini", "aktif", "berlaku"]
        )

        if is_historical and is_current:
            return TemporalMode.MIXED
        if is_historical:
            return TemporalMode.HISTORICAL
        return TemporalMode.CURRENT

    def decompose(
        self,
        query: str,
        intents: List[IntentType],
        temporal_mode: TemporalMode,
        k: int = 10,
    ) -> List[SubQueryTask]:
        tasks = []
        intent_to_agent = {
            IntentType.ACADEMIC: "academic",
            IntentType.SCHEDULE: "schedule",
            IntentType.ADMINISTRATION: "administration",
        }

        intent_to_namespace = {
            IntentType.ACADEMIC: ["active_academic"],
            IntentType.SCHEDULE: {
                TemporalMode.CURRENT: ["active_schedule", "active_dynamic_schedule"],
                TemporalMode.HISTORICAL: ["archive_schedule"],
                TemporalMode.MIXED: ["active_schedule", "active_dynamic_schedule", "archive_schedule"],
            },
            IntentType.ADMINISTRATION: ["active_administration"],
        }

        for intent in intents:
            agent_id = intent_to_agent[intent]
            ns_config = intent_to_namespace[intent]

            if isinstance(ns_config, dict):
                namespaces = ns_config.get(temporal_mode, ns_config[TemporalMode.CURRENT])
            else:
                namespaces = ns_config

            tasks.append(
                SubQueryTask(
                    sub_query=query,
                    agent=agent_id,
                    namespace=namespaces,
                    temporal_mode=temporal_mode,
                    k=k,
                )
            )

        return tasks

    def route_and_process(self, query: str, k: int = 10) -> RoutingDecision:
        intents = self.classify_intents(query)
        temporal_mode = self.classify_temporal_mode(query)
        tasks = self.decompose(query, intents, temporal_mode, k=k)

        return RoutingDecision(
            intents=intents,
            temporal_mode=temporal_mode,
            agents=[t.agent for t in tasks],
            subqueries=tasks,
            response_mode=ResponseMode.ANSWER,
        )

    def route_request(self, query: str) -> BackwardCompatRoutingDecision:
        """Backward compatibility method for single-agent tests."""
        intents = self.classify_intents(query)
        primary_agent = "academic"
        if IntentType.SCHEDULE in intents:
            primary_agent = "schedule"
        elif IntentType.ADMINISTRATION in intents:
            primary_agent = "admin"

        return BackwardCompatRoutingDecision(
            agent_id=primary_agent,
            confidence=0.9,
            reason=f"Routed to {primary_agent}",
        )

    def process_request(self, query: str) -> Dict[str, Any]:
        """Backward compatibility method for tests."""
        routing = self.route_and_process(query)
        agent_results = self.execute_agents(routing)
        merged = self.merge_results(agent_results)
        return {
            "agent": merged.agent,
            "status": merged.status.value if hasattr(merged.status, "value") else str(merged.status),
            "evidence": merged.evidence,
            "draft_answer": merged.draft_answer,
            "unresolved_flags": merged.unresolved_flags,
            "handoff": merged.handoff,
            "confidence": merged.confidence,
        }

    def execute_agents(self, routing: RoutingDecision) -> List[AgentResult]:
        results = []

        for task in routing.subqueries:
            agent = _AGENTS.get(task.agent)
            if not agent:
                logger.error(f"Unknown agent: {task.agent}")
                results.append(
                    AgentResult(
                        agent=task.agent,
                        status=AgentStatus.ERROR,
                        response_mode=ResponseMode.ERROR,
                    )
                )
                continue

            try:
                result = agent.process(task)
                results.append(result)
            except Exception as e:
                logger.error(f"Agent {task.agent} failed: {e}")
                results.append(
                    AgentResult(
                        agent=task.agent,
                        status=AgentStatus.ERROR,
                        response_mode=ResponseMode.ERROR,
                    )
                )

        return results

    def merge_results(self, results: List[AgentResult]) -> AgentResult:
        if not results:
            return AgentResult(
                agent="coordinator",
                status=AgentStatus.ERROR,
                response_mode=ResponseMode.ERROR,
            )

        if len(results) == 1:
            return results[0]

        all_evidence: List[Evidence] = []
        seen_chunks: set = set()
        all_flags: List[str] = []
        agents_involved: List[str] = []
        handoffs: List[str] = []

        for r in results:
            agents_involved.append(r.agent)
            all_flags.extend(r.unresolved_flags)
            if r.handoff:
                handoffs.append(r.handoff)
            for ev in r.evidence:
                if ev.chunk_id not in seen_chunks:
                    seen_chunks.add(ev.chunk_id)
                    all_evidence.append(ev)

        all_evidence.sort(key=lambda e: (-e.score, e.chunk_id))
        merged_mode = self._merge_response_modes([r.response_mode for r in results])

        drafts = [r.draft_answer for r in results if r.draft_answer]
        merged_draft = "\n\n".join(drafts)
        max_conf = max(r.confidence for r in results) if results else 0.0

        return AgentResult(
            agent=", ".join(agents_involved),
            status=AgentStatus.SUCCESS if any(r.status == AgentStatus.SUCCESS for r in results) else AgentStatus.PARTIAL,
            draft_answer=merged_draft,
            evidence=all_evidence,
            unresolved_flags=all_flags,
            handoff="; ".join(handoffs) if handoffs else None,
            confidence=max_conf,
            response_mode=merged_mode,
        )

    def _merge_response_modes(self, modes: List[ResponseMode]) -> ResponseMode:
        priority = [
            ResponseMode.REFUSE,
            ResponseMode.ESCALATE,
            ResponseMode.HANDOFF,
            ResponseMode.ABSTAIN,
            ResponseMode.LIVE_CHECK_OR_ABSTAIN,
            ResponseMode.ASK_CONTEXT,
            ResponseMode.ANSWER,
        ]
        for p in priority:
            if p in modes:
                return p
        return ResponseMode.ANSWER


coordinator = Coordinator()
