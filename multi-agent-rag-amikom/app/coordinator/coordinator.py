from typing import Dict, Any
from app.schemas.routing import RoutingDecision
from app.agents.academic import academic_agent
from app.agents.schedule import schedule_agent
from app.agents.admin import admin_agent
from app.observability import logger

class Coordinator:
    def __init__(self):
        self.agents = {
            "academic": academic_agent,
            "schedule": schedule_agent,
            "admin": admin_agent
        }

    def route_request(self, query: str) -> RoutingDecision:
        query_lower = query.lower()
        
        # Simple heuristic routing
        if any(kw in query_lower for kw in ["jadwal", "tanggal", "ujian", "kalender"]):
            return RoutingDecision(agent_id="schedule", confidence=0.9, reason="Keywords match schedule")
            
        if any(kw in query_lower for kw in ["cuti", "surat", "administrasi", "login"]):
            return RoutingDecision(agent_id="admin", confidence=0.9, reason="Keywords match administration")
            
        # Default to academic
        return RoutingDecision(agent_id="academic", confidence=0.8, reason="Defaulting to academic agent")

    def process_request(self, query: str) -> Dict[str, Any]:
        decision = self.route_request(query)
        logger.info(f"Routed to {decision.agent_id} with confidence {decision.confidence}")
        
        agent = self.agents.get(decision.agent_id)
        if not agent:
            raise ValueError(f"Unknown agent: {decision.agent_id}")
            
        return agent.process_request(query)

coordinator = Coordinator()
