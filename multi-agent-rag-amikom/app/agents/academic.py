from typing import Dict, Any
from app.agents.base import BaseAgent
from app.observability import logger

class AcademicAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "Academic Agent"
        
    @property
    def allowed_namespaces(self) -> list[str]:
        return ["active_academic"]
        
    def process_request(self, query: str) -> Dict[str, Any]:
        logger.info(f"{self.name} processing query: {query}")
        evidence = self.retrieve_evidence(query)
        
        return {
            "agent": self.name,
            "status": "SUCCESS",
            "evidence": evidence
        }

academic_agent = AcademicAgent()
