"""Stage runner: Retrieval Test for the 30 CORE + 6 SUPPLEMENTARY evaluation set."""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ragx import control, encoder, retriever, store  # noqa: E402

WIB = dt.timezone(dt.timedelta(hours=7))
OUT = "/home/claude/work/out"
CKPT = os.path.join(OUT, "checkpoints")
os.makedirs(CKPT, exist_ok=True)

K_LIST = [1, 3, 5, 10]
EVAL_CSV = os.path.join(
    store.CHUNK_BASE, "00_manifest", "evaluation_chunk_coverage.csv"
)


def now():
    return dt.datetime.now(WIB).isoformat()


def load_eval():
    with open(EVAL_CSV, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    con = store.open_db()
    records = store.load_all(con)
    idx = retriever.BM25Index(records)
    by_chunk = {r.chunk_id: r for r in records}
    ctl = store.load_control_registry()
    print(f"control registry loaded: "
          f"{ {k: len(v) for k, v in ctl.items()} }")

    rows = load_eval()
    results = {"CORE": [], "SUPPLEMENTARY": []}
    t_start = time.perf_counter()

    for n, r in enumerate(rows, 1):
        ev = r["evaluation_id"]
        question = r["question"]
        gold_all = [c for c in r["expected_chunk_ids"].split("|")
                    if c and c != "NOT_APPLICABLE"]
        gold_db = [c for c in gold_all if c in by_chunk]
        gold_control_only = [c for c in gold_all if c not in by_chunk]

        t0 = time.perf_counter()
        d = control.route(question)
        t_control = (time.perf_counter() - t0) * 1000.0

        formatted = encoder.format_query(question)
        qv = encoder.query_vector_status()

        t0 = time.perf_counter()
        if d.allow_factual_retrieval and d.namespaces:
            if d.retrieval_mode == "HISTORICAL":
                cands = store.candidate_indexes(con, d.namespaces, "HISTORICAL")
            elif d.retrieval_mode == "MIXED":
                cands = store.candidate_indexes(
                    con, [n_ for n_ in d.namespaces if n_ == "archive_schedule"],
                    "HISTORICAL")
                cands += store.candidate_indexes(
                    con, [n_ for n_ in d.namespaces if n_ != "archive_schedule"],
                    "CURRENT")
            else:
                cands = store.candidate_indexes(con, d.namespaces, "CURRENT")
        else:
            cands = []
        t_filter = (time.perf_counter() - t0) * 1000.0

        per_k = {}
        for k in K_LIST:
            hits, ms = retriever.retrieve(idx, question, sorted(set(cands)), k)
            recs = [by_chunk[h.chunk_id] for h in hits]
            archive_hits = [h.chunk_id for h, rec in zip(hits, recs)
                            if rec.lifecycle_status == "ARCHIVE"]
            fresh = []
            for h, rec in zip(hits, recs):
                fc = control.freshness_check(rec)
                if fc["expired"] or rec.lifecycle_status == "ACTIVE_DYNAMIC":
                    fresh.append({"chunk_id": h.chunk_id, **fc})
            per_k[str(k)] = {
                "retrieved_chunk_ids": [h.chunk_id for h in hits],
                "retrieved_vector_indexes": [h.vector_index for h in hits],
                "similarity_scores": [h.score for h in hits],
                "normalized_scores": [h.normalized_score for h in hits],
                "ranks": [h.rank for h in hits],
                "retrieved_source_ids": [rec.source_id for rec in recs],
                "retrieved_namespaces": [rec.retrieval_namespace for rec in recs],
                "retrieved_lifecycles": [rec.lifecycle_status for rec in recs],
                "archive_hits": archive_hits,
                "freshness_flags": fresh,
                "retrieval_latency_ms": round(ms, 3),
                "latency_ms": round(t_control + t_filter + ms, 3),
            }

        rec_out = {
            "evaluation_id": ev,
            "test_set": r["test_set"],
            "category": r["category"],
            "question": question,
            "formatted_query": formatted,
            "query_vector": qv,
            "retriever_backend": retriever.BACKEND,
            "expected_agent": r["expected_agent"],
            "expected_domain": r["category"],
            "expected_source_id": r["expected_source_id"],
            "expected_chunk_ids": gold_all,
            "expected_chunk_ids_in_db": gold_db,
            "expected_chunk_ids_control_only": gold_control_only,
            "expected_response_mode": r["expected_response_mode"],
            "expected_control_id": r["expected_control_id"],
            "expected_guardrail_action": r["expected_guardrail_action"],
            "expected_handoff_required": r["handoff_required"],
            "expected_auth_required": r["authentication_required"],
            "expected_live_check_required": r["live_check_required"],
            "coverage_status": r["coverage_status"],
            "gold_section": r["gold_section"],
            "gold_answer": r["gold_answer"],
            "routing_domain": d.routing_domain,
            "predicted_agent": d.expected_agent,
            "applied_filter": {
                "mode": d.retrieval_mode,
                "namespaces": d.namespaces,
                "sql_predicate": (
                    "active_retrieval_allowed=1 AND historical_only=0 AND "
                    f"retrieval_namespace IN {tuple(d.namespaces)}"
                    if d.retrieval_mode == "CURRENT" else
                    "historical_only=1 AND lifecycle_status='ARCHIVE' AND "
                    f"retrieval_namespace IN {tuple(d.namespaces)}"
                    if d.retrieval_mode == "HISTORICAL" else
                    f"MIXED over {tuple(d.namespaces)}"
                ),
                "candidate_count": len(set(cands)),
            },
            "control_triggered": d.control_triggered,
            "predicted_response_mode": d.response_mode,
            "predicted_guardrail_action": d.guardrail_action,
            "predicted_handoff_required": d.handoff_required,
            "predicted_handoff_target": d.handoff_target,
            "predicted_auth_required": d.authentication_required,
            "predicted_live_check_required": d.live_check_required,
            "partial_abstain": d.partial_abstain,
            "source_constraints": d.source_constraints,
            "control_notes": d.notes,
            "factual_retrieval_executed": bool(d.allow_factual_retrieval and cands),
            "retrieval_status": (
                "CONTROL_SHORT_CIRCUIT" if not d.allow_factual_retrieval
                else ("EXECUTED" if cands else "NO_CANDIDATE")
            ),
            "control_latency_ms": round(t_control, 3),
            "filter_latency_ms": round(t_filter, 3),
            "per_k": per_k,
            "executed_at_wib": now(),
        }
        results[r["test_set"]].append(rec_out)
        if n % 10 == 0:
            with open(os.path.join(CKPT, f"retrieval_ckpt_{n:03d}.json"), "w",
                      encoding="utf-8") as f:
                json.dump({"completed": n, "at": now()}, f)
            print(f"checkpoint at {n}")

    for name, key in (("Retrieval_Results_CORE.jsonl", "CORE"),
                      ("Retrieval_Results_SUPPLEMENTARY.jsonl", "SUPPLEMENTARY")):
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            for rec in results[key]:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(name, len(results[key]))

    print("total wall ms", round((time.perf_counter() - t_start) * 1000, 1))


if __name__ == "__main__":
    main()
