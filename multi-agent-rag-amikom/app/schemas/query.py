from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Pertanyaan mahasiswa AMIKOM")
    session_id: Optional[str] = Field(default="demo-session", description="ID sesi pengguna")
    user_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Konteks pengguna (misal cohort: 2025)")
    requested_mode: Optional[str] = Field(default="AUTO", description="Mode operasi yang diminta")
