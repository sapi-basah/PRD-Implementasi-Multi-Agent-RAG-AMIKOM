"""Pipeline service: mengintegrasikan seluruh tahapan sistem RAG multi-agent.

Flow:
User/API -> Pre-Control -> Coordinator -> Specialist Agent(s) -> Shared Retrieval -> LLM/Fallback -> Coordinator Merge -> Verifier -> Final Response
"""

import time
import uuid
from typing import Any, Dict

from app.config.settings import settings
from app.controls.pre_control import pre_control
from app.coordinator.coordinator import coordinator
from app.generator.llm import llm_generator
from app.observability import logger
from app.retrieval import shared_retrieval_service
from app.schemas import Citation, FinalResponse, ResponseMode, VerificationResult
from app.verifier.guardrail import final_verifier


class PipelineService:
    """End-to-end pipeline service untuk memproses query."""

    def process(self, query: str, session_id: str = "demo-session") -> Dict[str, Any]:
        start_time = time.time()
        request_id = str(uuid.uuid4())
        logger.info(f"Pipeline processing request_id={request_id} query='{query}'")

        # 1. Pre-Control
        pre_res = pre_control.validate_request(query)
        if pre_res.short_circuit:
            latency_ms = (time.time() - start_time) * 1000
            logger.info(f"Pre-control short-circuit: mode={pre_res.response_mode} reason='{pre_res.reason}'")
            return {
                "request_id": request_id,
                "mode": pre_res.response_mode,
                "answer": pre_res.reason,
                "citations": [],
                "freshness_notice": None,
                "handoff": pre_res.handoff,
                "retrieval_backend": shared_retrieval_service.backend_name,
                "generation_backend": "PRE_CONTROL",
                "agents_involved": [],
                "intent": [],
                "temporal_mode": "CURRENT",
                "verification": {
                    "status": "PASS",
                    "checks": [
                        {
                            "check_name": "pre_control",
                            "status": "SHORT_CIRCUIT",
                            "message": pre_res.reason,
                        }
                    ],
                },
                "latency_ms": round(latency_ms, 2),
                "system_readiness": "DEVELOPMENT_READY",
                # Backward compatibility for flat API
                "query": query,
                "agent_used": None,
                "metadata": {
                    "response_mode": pre_res.response_mode,
                    "control_flags": pre_res.control_flags,
                    "processing_time_ms": int(latency_ms),
                    "warning": None,
                },
            }

        # 2. Coordinator Routing & Agent Execution
        try:
            routing = coordinator.route_and_process(query, k=settings.RETRIEVAL_TOP_K)
            agent_results = coordinator.execute_agents(routing)
            merged_result = coordinator.merge_results(agent_results)
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Coordinator execution failed: {e}")
            return {
                "request_id": request_id,
                "mode": ResponseMode.ERROR.value,
                "answer": "Terjadi kesalahan internal pada sistem routing/retrieval.",
                "citations": [],
                "freshness_notice": None,
                "handoff": None,
                "retrieval_backend": shared_retrieval_service.backend_name,
                "generation_backend": "NONE",
                "agents_involved": [],
                "intent": [],
                "temporal_mode": "CURRENT",
                "verification": {
                    "status": "FAIL",
                    "checks": [
                        {
                            "check_name": "coordinator",
                            "status": "ERROR",
                            "message": str(e),
                        }
                    ],
                },
                "latency_ms": round(latency_ms, 2),
                "system_readiness": "DEGRADED",
                "query": query,
                "agent_used": None,
                "metadata": {
                    "response_mode": ResponseMode.ERROR.value,
                    "control_flags": [],
                    "processing_time_ms": int(latency_ms),
                    "warning": str(e),
                },
            }

        # Check if merged result is non-ANSWER mode (e.g., ESCALATE, ABSTAIN, REFUSE, HANDOFF)
        if merged_result.response_mode != ResponseMode.ANSWER:
            latency_ms = (time.time() - start_time) * 1000
            answer_text = merged_result.draft_answer or "Informasi tidak dapat diproses."
            if merged_result.response_mode == ResponseMode.ABSTAIN:
                answer_text = "Maaf, informasi yang Anda tanyakan belum tersedia dalam sistem resmi."
            elif merged_result.response_mode == ResponseMode.ESCALATE:
                answer_text = "Terdapat ambiguitas aturan atau konflik informasi. Harap eskalasi ke DPA atau BAAK."
            elif merged_result.response_mode == ResponseMode.REFUSE:
                answer_text = "Pertanyaan ini di luar cakupan layanan atau memerlukan otentikasi data pribadi."

            return {
                "request_id": request_id,
                "mode": merged_result.response_mode.value,
                "answer": answer_text,
                "citations": [],
                "freshness_notice": None,
                "handoff": merged_result.handoff,
                "retrieval_backend": shared_retrieval_service.backend_name,
                "generation_backend": "COORDINATOR",
                "agents_involved": [merged_result.agent],
                "intent": [i.value for i in routing.intents],
                "temporal_mode": routing.temporal_mode.value,
                "verification": {
                    "status": "PASS",
                    "checks": [
                        {
                            "check_name": "agent_response_mode",
                            "status": "NON_ANSWER",
                            "message": f"Mode: {merged_result.response_mode.value}",
                        }
                    ],
                },
                "latency_ms": round(latency_ms, 2),
                "system_readiness": "DEVELOPMENT_READY",
                "query": query,
                "agent_used": merged_result.agent,
                "metadata": {
                    "response_mode": merged_result.response_mode.value,
                    "control_flags": merged_result.unresolved_flags,
                    "processing_time_ms": int(latency_ms),
                    "warning": None,
                },
            }

        # 3. Agent & Pre-Generation Verification
        agent_verification = final_verifier.verify_agent_result(
            merged_result, temporal_mode=routing.temporal_mode.value
        )
        if agent_verification.response_mode_override:
            merged_result.response_mode = agent_verification.response_mode_override

        # 4. Generation (LLM or Evidence Selector V2)
        try:
            gen_res = llm_generator.generate(
                query,
                merged_result.evidence,
                response_mode=merged_result.response_mode.value,
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Generation failed: {e}")
            return {
                "request_id": request_id,
                "mode": ResponseMode.ERROR.value,
                "answer": "Terjadi kesalahan saat menghasilkan jawaban.",
                "citations": [],
                "freshness_notice": None,
                "handoff": None,
                "retrieval_backend": shared_retrieval_service.backend_name,
                "generation_backend": "FAILED",
                "agents_involved": [merged_result.agent],
                "intent": [i.value for i in routing.intents],
                "temporal_mode": routing.temporal_mode.value,
                "verification": {
                    "status": "FAIL",
                    "checks": [
                        {
                            "check_name": "generator",
                            "status": "ERROR",
                            "message": str(e),
                        }
                    ],
                },
                "latency_ms": round(latency_ms, 2),
                "system_readiness": "DEGRADED",
                "query": query,
                "agent_used": merged_result.agent,
                "metadata": {
                    "response_mode": ResponseMode.ERROR.value,
                    "control_flags": [],
                    "processing_time_ms": int(latency_ms),
                    "warning": str(e),
                },
            }

        raw_answer = gen_res.get("answer", "")
        raw_citations = gen_res.get("citations", [])

        # Format citations to dict list
        citations_list = []
        for cit in raw_citations:
            if isinstance(cit, Citation):
                citations_list.append(cit.model_dump())
            elif isinstance(cit, dict):
                citations_list.append(cit)

        # 5. Final Post-Generation Verification
        typed_citations = [
            Citation(**c) if isinstance(c, dict) else c for c in citations_list
        ]
        post_verification = final_verifier.verify_final_response(
            raw_answer, typed_citations, merged_result.evidence
        )

        final_mode = merged_result.response_mode.value
        if post_verification.response_mode_override:
            final_mode = post_verification.response_mode_override.value

        # Redact PII if verifier detected PII in output
        final_answer = raw_answer
        if any(c.check_name == "pii_in_output" for c in post_verification.checks):
            final_answer = final_verifier.redact_pii_from_output(raw_answer)

        # Freshness notice if dynamic schedule chunk present
        freshness_notice = None
        for ev in merged_result.evidence:
            if ev.retrieval_namespace == "active_dynamic_schedule":
                freshness_notice = "Catatan: Informasi jadwal ini dapat berubah sewaktu-waktu. Cek portal resmi AMIKOM secara berkala."
                break

        latency_ms = (time.time() - start_time) * 1000

        # Combine checks
        all_checks = [
            c.model_dump() for c in agent_verification.checks
        ] + [c.model_dump() for c in post_verification.checks]

        verifier_status = (
            "PASS"
            if agent_verification.status == "PASS"
            and post_verification.status == "PASS"
            else "FAIL"
        )

        return {
            "request_id": request_id,
            "mode": final_mode,
            "answer": final_answer,
            "citations": citations_list,
            "freshness_notice": freshness_notice,
            "handoff": merged_result.handoff,
            "retrieval_backend": shared_retrieval_service.backend_name,
            "generation_backend": gen_res.get("generation_backend", "LLM"),
            "agents_involved": [merged_result.agent],
            "intent": [i.value for i in routing.intents],
            "temporal_mode": routing.temporal_mode.value,
            "verification": {
                "status": verifier_status,
                "checks": all_checks,
            },
            "latency_ms": round(latency_ms, 2),
            "system_readiness": "DEVELOPMENT_READY",
            "query": query,
            "agent_used": merged_result.agent,
            "metadata": {
                "response_mode": final_mode,
                "control_flags": merged_result.unresolved_flags,
                "processing_time_ms": int(latency_ms),
                "warning": None,
            },
        }


pipeline_service = PipelineService()
