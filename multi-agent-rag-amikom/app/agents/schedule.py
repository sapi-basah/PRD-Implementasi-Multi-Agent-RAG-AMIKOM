from typing import Dict, Any
from app.agents.base import BaseAgent
from app.observability import logger

class ScheduleAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "Schedule Agent"
        
    @property
    def allowed_namespaces(self) -> list[str]:
        return ["active_schedule", "active_dynamic_schedule", "archive_schedule"]
        
    def process_request(self, query: str) -> Dict[str, Any]:
        logger.info(f"{self.name} processing query: {query}")
        
        # Schedule might need historical data if explicitly requested, but we default to active
        # The routing logic could pass a flag, but we'll keep it simple for now
        evidence = self.retrieve_evidence(query)
        
        return {
            "agent": self.name,
            "status": "SUCCESS",
            "evidence": evidence
        }

schedule_agent = ScheduleAgent()
