"""Administration Agent: prosedur administrasi akademik.

Tanggung jawab:
- KRS manual, cuti, SKAK, legalisir, KTM, perubahan data PDDIKTI
- Namespace: active_administration saja
- TIDAK memproses nilai, status transaksi, dokumen personal, data identitas aktual
"""

from app.agents.base import BaseAgent
from app.observability import logger
from app.schemas import (
    AgentResult,
    AgentStatus,
    ResponseMode,
    SubQueryTask,
)


# Keywords yang menunjukkan request data personal (ditolak)
_PERSONAL_KEYWORDS = [
    "nilai saya", "transkrip saya", "ipk saya",
    "status pembayaran", "tagihan", "bukti bayar",
    "ktp", "dokumen identitas", "password",
]


class AdminAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "AdministrationAgent"

    @property
    def allowed_namespaces(self) -> list[str]:
        return ["active_administration"]

    def process(self, task: SubQueryTask) -> AgentResult:
        logger.info(f"{self.name} processing: {task.sub_query[:80]}")

        # Check for personal data request
        query_lower = task.sub_query.lower()
        for kw in _PERSONAL_KEYWORDS:
            if kw in query_lower:
                return AgentResult(
                    agent=self.name,
                    status=AgentStatus.REFUSED,
                    draft_answer="",
                    evidence=[],
                    unresolved_flags=["PERSONAL_DATA_REQUEST"],
                    handoff="Silakan hubungi BAAK atau akses dashboard mahasiswa.",
                    confidence=0.0,
                    response_mode=ResponseMode.HANDOFF,
                )

        namespaces = task.namespace if task.namespace else self.allowed_namespaces
        evidence = self.retrieve_evidence(task.sub_query, namespaces=namespaces, k=task.k)
        draft = self._build_draft_answer(evidence)

        return AgentResult(
            agent=self.name,
            status=AgentStatus.SUCCESS if evidence else AgentStatus.PARTIAL,
            draft_answer=draft,
            evidence=evidence,
            unresolved_flags=[],
            confidence=max(ev.score for ev in evidence) if evidence else 0.0,
            response_mode=ResponseMode.ANSWER if evidence else ResponseMode.ABSTAIN,
        )


admin_agent = AdminAgent()
