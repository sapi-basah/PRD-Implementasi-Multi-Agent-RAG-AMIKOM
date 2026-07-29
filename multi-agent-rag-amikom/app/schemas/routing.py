from pydantic import BaseModel, Field

class RoutingDecision(BaseModel):
    agent_id: str = Field(description="The identifier of the selected agent")
    confidence: float = Field(description="Confidence score of the routing decision")
    reason: str = Field(description="Reason for selecting this agent")
