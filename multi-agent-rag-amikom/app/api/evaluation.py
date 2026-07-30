"""Evaluation API router (POST /api/v1/evaluation/run & GET /api/v1/evaluation/report)."""

import json
import os
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.config.settings import settings
from app.evaluation.runner import run_evaluation

router = APIRouter(tags=["Evaluation"])


@router.post("/api/v1/evaluation/run")
@router.post("/api/evaluation/run")
def trigger_evaluation(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    background_tasks.add_task(run_evaluation)
    return {
        "status": "QUEUED",
        "message": "Evaluasi telah dimasukkan ke dalam antrean latar belakang.",
    }


@router.get("/api/v1/evaluation/report")
@router.get("/api/evaluation/report")
def get_evaluation_report() -> Dict[str, Any]:
    report_path = os.path.join(settings.DATA_ROOT, "../../var/results/final_metrics.json")
    if not os.path.exists(report_path):
        report_path = "./evaluation_report.json"

    if not os.path.exists(report_path):
        return {
            "total_cases": 0,
            "pass_rate": 0.0,
            "status": "NO_REPORT",
            "details": [],
        }

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read report: {e}")
