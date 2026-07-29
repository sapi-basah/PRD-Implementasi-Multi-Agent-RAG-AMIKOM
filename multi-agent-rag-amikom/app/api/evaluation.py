from fastapi import APIRouter
from pydantic import BaseModel
import json
import os
from app.config import settings

router = APIRouter()

class EvaluationReport(BaseModel):
    total_cases: int
    pass_rate: float
    details: list

@router.get("/evaluation/report", response_model=EvaluationReport)
def get_evaluation_report():
    report_path = os.path.join(settings.BASE_DIR, "evaluation_report.json")
    if not os.path.exists(report_path):
        return EvaluationReport(total_cases=0, pass_rate=0.0, details=[])
        
    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    return EvaluationReport(
        total_cases=data.get("total_cases", 0),
        pass_rate=data.get("pass_rate", 0.0),
        details=data.get("details", [])
    )
