from typing import Dict, Any
from app.agents.base import BaseAgent
from app.observability import logger

class AdminAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "Admin Agent"
        
    @property
    def allowed_namespaces(self) -> list[str]:
        return ["active_administration"]
        
    def process_request(self, query: str) -> Dict[str, Any]:
        logger.info(f"{self.name} processing query: {query}")
        evidence = self.retrieve_evidence(query)
        
        return {
            "agent": self.name,
            "status": "SUCCESS",
            "evidence": evidence
        }

admin_agent = AdminAgent()
