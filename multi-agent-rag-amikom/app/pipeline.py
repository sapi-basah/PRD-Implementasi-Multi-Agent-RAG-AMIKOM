import time
from typing import Dict, Any
from app.controls.pre_control import pre_control
from app.coordinator.coordinator import coordinator
from app.generator.llm import llm_generator
from app.verifier.guardrail import final_verifier
from app.observability import logger

class PipelineService:
    def process(self, query: str) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"Processing query: {query}")
        
        # 1. Pre-control
        pre_res = pre_control.validate_request(query)
        if pre_res.short_circuit:
            logger.info(f"Short-circuited: {pre_res.reason}")
            return {
                "query": query,
                "answer": pre_res.reason,
                "citations": [],
                "agent_used": None,
                "metadata": {
                    "response_mode": pre_res.response_mode,
                    "control_flags": pre_res.control_flags,
                    "processing_time_ms": int((time.time() - start_time) * 1000)
                }
            }
            
        # 2. Coordinator & Retrieval (via Specialist Agents)
        try:
            agent_res = coordinator.process_request(query)
            evidences = agent_res.get("evidence", [])
            agent_name = agent_res.get("agent")
        except Exception as e:
            logger.error(f"Coordinator failed: {e}")
            return {
                "query": query,
                "answer": "Terjadi kesalahan internal pada sistem routing/retrieval.",
                "citations": [],
                "agent_used": None,
                "metadata": {
                    "response_mode": "ERROR",
                    "processing_time_ms": int((time.time() - start_time) * 1000)
                }
            }
            
        # 3. Generation
        try:
            gen_res = llm_generator.generate(query, evidences)
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return {
                "query": query,
                "answer": "Terjadi kesalahan internal saat menghasilkan jawaban.",
                "citations": [],
                "agent_used": agent_name,
                "metadata": {
                    "response_mode": "ERROR",
                    "processing_time_ms": int((time.time() - start_time) * 1000)
                }
            }
            
        # 4. Final Verifier
        final_res = final_verifier.verify(gen_res)
        
        return {
            "query": query,
            "answer": final_res["answer"],
            "citations": final_res["citations"],
            "agent_used": agent_name,
            "metadata": {
                "response_mode": "AUTO",
                "warning": final_res.get("warning"),
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
        }

pipeline_service = PipelineService()
