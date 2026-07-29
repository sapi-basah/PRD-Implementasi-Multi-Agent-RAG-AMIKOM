from typing import Dict, Any
import re
from app.observability import logger

class FinalVerifier:
    def verify(self, generator_output: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Running Final Verifier...")
        answer = generator_output.get("answer", "")
        
        # 1. Hallucination Check (Heuristic: no "saya tidak tahu" if we have citations)
        if "tidak menemukan informasi" in answer and generator_output.get("citations"):
            logger.warning("Guardrail: Contradiction detected (citations present but answer says none)")
            # In a real system, we'd flag for review or regenerate. We'll just append a warning.
            generator_output["warning"] = "Possible hallucination: citations found but answer claims ignorance."
            
        # 2. PII Check on the output (prevent leakage)
        # We can reuse the PII_PATTERNS from pre_control if we wanted, but let's just do a simple check
        if re.search(r'\b\d{16}\b', answer): # KTP or CC
            logger.error("Guardrail: PII detected in output. Redacting.")
            generator_output["answer"] = re.sub(r'\b\d{16}\b', '[REDACTED]', answer)
            generator_output["warning"] = "PII redacted from output."
            
        return generator_output

final_verifier = FinalVerifier()
