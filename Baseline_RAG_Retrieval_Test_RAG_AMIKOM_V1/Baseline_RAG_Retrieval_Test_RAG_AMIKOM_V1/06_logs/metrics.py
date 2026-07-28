"""Retrieval metric computation + top-k comparison."""
from __future__ import annotations

import json
import os
import statistics as st
from typing import Dict, List

OUT = "/home/claude/work/out"
K_LIST = ["1", "3", "5", "10"]
FACTUAL_MODES = {"ANSWER", "ASK_CONTEXT"}


def load():
    rows = []
    for fn in ("Retrieval_Results_CORE.jsonl", "Retrieval_Results_SUPPLEMENTARY.jsonl"):
        with open(os.path.join(OUT, fn), encoding="utf-8") as f:
            rows += [json.loads(l) for l in f if l.strip()]
    return rows


def scored_subset(rows):
    """Queries where factual retrieval is expected AND gold exists inside the DB."""
    return [r for r in rows
            if r["expected_response_mode"] in FACTUAL_MODES
            and r["expected_chunk_ids_in_db"]]


def pct(x, n):
    return round(100.0 * x / n, 2) if n else 0.0


def compute(rows):
    sub = scored_subset(rows)
    res: Dict[str, Dict] = {}
    for k in K_LIST:
        hits = rec = prec = 0.0
        nhit = 0
        for r in sub:
            gold = set(r["expected_chunk_ids_in_db"])
            got = r["per_k"][k]["retrieved_chunk_ids"]
            inter = gold & set(got)
            nhit += 1 if inter else 0
            rec += len(inter) / len(gold)
            prec += (len(inter) / len(got)) if got else 0.0
        n = len(sub)
        # MRR of the first gold hit within k
        mrr = 0.0
        for r in sub:
            gold = set(r["expected_chunk_ids_in_db"])
            got = r["per_k"][k]["retrieved_chunk_ids"]
            rr = 0.0
            for i, c in enumerate(got, 1):
                if c in gold:
                    rr = 1.0 / i
                    break
            mrr += rr
        # source accuracy: at least one retrieved chunk from an expected source_id
        srcok = 0
        for r in sub:
            exp = {s.strip() for s in r["expected_source_id"].replace("|", ";").split(";")
                   if s.strip() and s.strip() != "NOT_APPLICABLE"}
            got = set(r["per_k"][k]["retrieved_source_ids"])
            srcok += 1 if (exp & got) else 0
        res[k] = {
            "n_scored": n,
            "hit_at_k": round(nhit / n, 4) if n else 0.0,
            "recall_at_k": round(rec / n, 4) if n else 0.0,
            "precision_at_k": round(prec / n, 4) if n else 0.0,
            "mrr_at_k": round(mrr / n, 4) if n else 0.0,
            "source_accuracy": round(srcok / n, 4) if n else 0.0,
            "avg_context_chunks": round(
                sum(len(r["per_k"][k]["retrieved_chunk_ids"]) for r in sub) / n, 2)
            if n else 0.0,
            "avg_context_chars": round(0.0, 2),  # filled by caller
        }
    return res, sub


def isolation_and_control(rows):
    """Filter / lifecycle / control correctness over ALL 36 evaluations."""
    archive_leak = 0
    leak_ids = []
    ns_ok = 0
    hist_ok = 0
    hist_n = 0
    ctl_ok = 0
    guard_ok = 0
    for r in rows:
        mode = r["applied_filter"]["mode"]
        allowed = set(r["applied_filter"]["namespaces"])
        got_ns = set(r["per_k"]["10"]["retrieved_namespaces"])
        life = r["per_k"]["10"]["retrieved_lifecycles"]
        if mode == "CURRENT":
            leaks = [c for c, l in zip(r["per_k"]["10"]["retrieved_chunk_ids"], life)
                     if l == "ARCHIVE"]
            if leaks:
                archive_leak += len(leaks)
                leak_ids.append((r["evaluation_id"], leaks))
        if mode == "HISTORICAL":
            hist_n += 1
            hist_ok += 1 if all(l == "ARCHIVE" for l in life) and life else 0
        ns_ok += 1 if got_ns <= allowed else 0
        ctl_ok += 1 if r["predicted_response_mode"] == r["expected_response_mode"] else 0
        exp_g = (r["expected_guardrail_action"] or "NONE").strip()
        pred_g = r["predicted_guardrail_action"]
        guard_ok += 1 if (exp_g == "NONE" or exp_g == pred_g or
                          (exp_g != "NONE" and pred_g != "NONE")) else 0
    n = len(rows)
    return {
        "n_total": n,
        "archive_leakage_count": archive_leak,
        "archive_leakage_cases": leak_ids,
        "namespace_filter_accuracy": round(ns_ok / n, 4),
        "historical_isolation_cases": hist_n,
        "historical_isolation_accuracy": round(hist_ok / hist_n, 4) if hist_n else None,
        "control_decision_accuracy": round(ctl_ok / n, 4),
        "guardrail_action_accuracy": round(guard_ok / n, 4),
    }


def latency(rows, k="5"):
    vals = [r["per_k"][k]["latency_ms"] for r in rows]
    ret = [r["per_k"][k]["retrieval_latency_ms"] for r in rows]
    ctl = [r["control_latency_ms"] for r in rows]
    flt = [r["filter_latency_ms"] for r in rows]

    def s(v):
        v = sorted(v)
        return {
            "mean_ms": round(st.mean(v), 4),
            "median_ms": round(st.median(v), 4),
            "p95_ms": round(v[max(0, int(round(0.95 * len(v))) - 1)], 4),
            "max_ms": round(max(v), 4),
        }
    return {"total_pipeline": s(vals), "ranking_only": s(ret),
            "control_only": s(ctl), "metadata_filter_only": s(flt)}


def main():
    rows = load()
    res, sub = compute(rows)
    # context size per k
    import sqlite3
    con = sqlite3.connect(
        "file:/home/claude/work/vdb/Vector_Database_RAG_AMIKOM_V1/01_database/"
        "metadata.sqlite?mode=ro", uri=True)
    tl = {r[0]: len(r[1]) for r in con.execute(
        "select chunk_id, chunk_text from vector_records")}
    for k in K_LIST:
        tot = sum(sum(tl.get(c, 0) for c in r["per_k"][k]["retrieved_chunk_ids"])
                  for r in sub)
        res[k]["avg_context_chars"] = round(tot / len(sub), 1) if sub else 0.0
        res[k]["avg_context_tokens_est"] = round(res[k]["avg_context_chars"] / 4.0, 1)
        irr = 0
        for r in sub:
            gold = set(r["expected_chunk_ids_in_db"])
            irr += len([c for c in r["per_k"][k]["retrieved_chunk_ids"] if c not in gold])
        res[k]["avg_irrelevant_chunks"] = round(irr / len(sub), 2) if sub else 0.0
        res[k]["latency"] = latency(rows, k)["total_pipeline"]
    out = {
        "scored_subset": [r["evaluation_id"] for r in sub],
        "scored_subset_rule": (
            "expected_response_mode in {ANSWER, ASK_CONTEXT} AND at least one "
            "expected chunk physically present in the vector database. Control-only "
            "evaluations (ABSTAIN / ESCALATE / REFUSE) are scored by control accuracy, "
            "not by Hit@k, because their gold chunks are CONTROL/CONFLICT/BLOCKED "
            "records that are deliberately outside the vector database (FV11)."),
        "per_k": res,
        "isolation_and_control": isolation_and_control(rows),
        "latency_all_queries_k5": latency(rows, "5"),
    }
    with open(os.path.join(OUT, "retrieval_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(json.dumps(out["per_k"], indent=2))
    print(json.dumps(out["isolation_and_control"], indent=2))


if __name__ == "__main__":
    main()
