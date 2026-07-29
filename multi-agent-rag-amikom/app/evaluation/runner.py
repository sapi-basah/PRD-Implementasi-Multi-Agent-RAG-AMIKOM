import os
import json
import time
from typing import List, Dict, Any
from app.config import settings
from app.pipeline import pipeline_service
from app.observability import logger

def run_evaluation():
    logger.info("Starting Multi-Agent RAG Evaluation Runner...")
    
    # 1. Load context packs to get questions
    packs_path = "./data/immutable/evaluation/Baseline_RAG_Retrieval_Test_RAG_AMIKOM_V1/02_results/context_packs.json"
    if not os.path.exists(packs_path):
        logger.error(f"context_packs.json not found at {packs_path}")
        return
        
    with open(packs_path, "r", encoding="utf-8") as f:
        packs_data = json.load(f)
        
    question_map = {pack["evaluation_id"]: pack["question"] for pack in packs_data.get("packs", [])}
    
    # 2. Load baseline evaluation to get expected modes
    baseline_path = "./data/immutable/evaluation/Baseline_RAG_Retrieval_Test_RAG_AMIKOM_V1/03_evaluation/baseline_rag_evaluation.json"
    if not os.path.exists(baseline_path):
        logger.error(f"baseline_rag_evaluation.json not found at {baseline_path}")
        return
        
    with open(baseline_path, "r", encoding="utf-8") as f:
        baseline_data = json.load(f)
        
    baseline_rows = baseline_data.get("rows", [])
    
    # 3. Run queries through pipeline
    details = []
    correct_count = 0
    
    for row in baseline_rows:
        eval_id = row["evaluation_id"]
        expected_mode = row["expected_response_mode"]
        question = question_map.get(eval_id)
        
        if not question:
            logger.warning(f"No question found for evaluation ID: {eval_id}")
            continue
            
        logger.info(f"Evaluating {eval_id}: '{question[:50]}...'")
        
        # Process query
        result = pipeline_service.process(question)
        applied_mode = result["metadata"]["response_mode"]
        
        # Assess correctness
        # Map our internal response modes to expected modes if necessary
        # expected modes: ANSWER, ESCALATE, ABSTAIN, REFUSE, ASK_CONTEXT
        is_correct = (applied_mode == expected_mode)
        
        if is_correct:
            correct_count += 1
            if expected_mode == "ANSWER":
                grade = "PASS"
            elif expected_mode == "ESCALATE":
                grade = "HANDOFF_CORRECT"
            elif expected_mode == "ABSTAIN":
                grade = "ABSTAIN_CORRECT"
            elif expected_mode == "REFUSE":
                grade = "OUT_OF_SCOPE_CORRECT"
            else:
                grade = "PASS"
        else:
            grade = "FAIL"
            
        details.append({
            "evaluation_id": eval_id,
            "question": question,
            "expected_response_mode": expected_mode,
            "response_mode_applied": applied_mode,
            "response_mode_correct": is_correct,
            "grade": grade,
            "answer": result["answer"],
            "processing_time_ms": result["metadata"]["processing_time_ms"]
        })
        
    pass_rate = correct_count / len(details) if details else 0.0
    
    report = {
        "total_cases": len(details),
        "pass_rate": pass_rate,
        "details": details
    }
    
    # Write report
    report_out_path = "./evaluation_report.json"
    with open(report_out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Evaluation completed. Pass rate: {pass_rate:.2%}. Report saved to {report_out_path}")

if __name__ == "__main__":
    run_evaluation()
