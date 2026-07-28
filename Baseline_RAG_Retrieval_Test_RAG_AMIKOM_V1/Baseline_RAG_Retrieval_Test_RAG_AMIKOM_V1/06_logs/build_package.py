"""Build every mandatory output artefact for the Retrieval / Baseline RAG stage."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import shutil

WIB = dt.timezone(dt.timedelta(hours=7))
OUT = "/home/claude/work/out"
PKG = "/home/claude/work/package/Baseline_RAG_Retrieval_Test_RAG_AMIKOM_V1"
NOW = dt.datetime.now(WIB).isoformat()

for sub in ("00_manifest", "01_config", "02_results", "03_evaluation", "04_qa",
            "05_checkpoint", "06_logs"):
    os.makedirs(os.path.join(PKG, sub), exist_ok=True)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def jload(p):
    return json.load(open(p, encoding="utf-8"))


def jlload(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


metrics = jload(os.path.join(OUT, "retrieval_metrics.json"))
evalj = jload(os.path.join(OUT, "baseline_rag_evaluation.json"))
dbval = jload(os.path.join(OUT, "database_validation.json"))
core = jlload(os.path.join(OUT, "Retrieval_Results_CORE.jsonl"))
supp = jlload(os.path.join(OUT, "Retrieval_Results_SUPPLEMENTARY.jsonl"))
answers = jlload(os.path.join(OUT, "Baseline_RAG_Answers.jsonl"))
checks = {c["evaluation_id"]: c
          for c in jload(os.path.join(OUT, "generation_autochecks.json"))}
allr = core + supp
BASELINE_K = 5

# ---------------------------------------------------------------- config json
config = {
    "package_name": "Baseline_RAG_Retrieval_Test_RAG_AMIKOM_V1",
    "stage": "BASELINE_RAG_AND_RETRIEVAL_TESTING",
    "created_at_wib": NOW,
    "scope_status": "FROZEN",
    "vector_database_gate": "PASS",
    "retrieval_testing": "PARTIALLY_COMPLETE",
    "baseline_rag": "COMPLETE",
    "baseline_top_k": BASELINE_K,
    "top_k_candidates_tested": [1, 3, 5, 10],
    "query_encoder": {
        "mandated_model_name": "Xenova/multilingual-e5-small",
        "mandated_model_revision": "761b726dd34fb83930e26aab4e9ac3899aa1fa78",
        "mandated_tokenizer": "XLMRobertaTokenizer - Xenova/multilingual-e5-small",
        "query_prefix": "query: ",
        "document_prefix_never_used_for_questions": "passage: ",
        "pooling_strategy": "mean",
        "normalize_embeddings": True,
        "embedding_dimension": 384,
        "embedding_dtype": "float32",
        "execution_status": "NOT_EXECUTED",
        "block_reason": dbval["query_encoder"]["reason"],
        "query_vectors_produced": 0,
    },
    "retriever_backend": {
        "backend_id": "FALLBACK_LEXICAL_BM25_V1",
        "algorithm": "BM25 Okapi",
        "k1": 1.5,
        "b": 0.75,
        "indexed_fields": ["title", "chunk_text"],
        "tokenizer": "lowercase + [a-z0-9]+ regex + Indonesian stopword list",
        "idf_corpus": "all 306 indexed records (static corpus statistic)",
        "scoring_scope": "SQLite candidate set only (filter before ranking)",
        "deterministic": True,
        "rationale": "Substitute retriever so that control, filter, metric and "
                     "generation layers can be exercised while the mandated E5 "
                     "encoder is unavailable. Scores are NOT cosine similarities.",
    },
    "vector_database": {
        "faiss_index": "01_database/faiss.index",
        "metadata_sqlite": "01_database/metadata.sqlite",
        "faiss_ntotal": dbval["faiss"]["ntotal"],
        "dimension": dbval["faiss"]["dimension"],
        "sqlite_records": dbval["sqlite"]["record_count"],
        "opened_read_only": True,
        "functional_smoke_test": dbval["faiss_functional_smoke_test"]["status"],
        "vector_search_executed_for_queries": False,
    },
    "metadata_filter": {
        "order": "control_check -> metadata_filter -> ranking -> top_k",
        "current_predicate": "active_retrieval_allowed=1 AND historical_only=0 AND "
                             "retrieval_namespace IN (routed active namespaces)",
        "historical_predicate": "historical_only=1 AND lifecycle_status='ARCHIVE' AND "
                                "retrieval_namespace='archive_schedule'",
        "active_namespaces": ["active_academic", "active_schedule",
                              "active_administration", "active_dynamic_schedule"],
        "archive_namespace": "archive_schedule",
        "global_topk_then_discard": False,
    },
    "control_layer": {
        "source": "Chunk_Corpus_RAG_AMIKOM_V1 CONTROL/CONFLICT/BLOCKED records only",
        "records_loaded": {"CONTROL": 10, "CONFLICT": 2, "BLOCKED": 1},
        "controls_enforced": ["INT01", "INT02", "INT03", "INT04", "INT05", "INT06",
                              "INT07", "G01", "G02", "CF001", "CF002",
                              "MR-A11-RELATIONS"],
        "control_as_vector_knowledge": False,
    },
    "freshness_policy": {
        "evaluation_time_wib": NOW,
        "active_dynamic_ttl_days": 1,
        "active_dynamic_snapshot_at_wib": "2026-07-24T23:50:04+07:00",
        "verdict": "EXPIRED -> response_mode LIVE_CHECK_OR_ABSTAIN",
    },
    "generator": {
        "type": "single generator LLM (no multi-agent, no coordinator, no verifier)",
        "model": "claude-opus-5",
        "prompt_contract": [
            "answer only from retrieved context",
            "no added facts",
            "cite source_id and locator",
            "say not found when context is insufficient",
            "obey ABSTAIN / ESCALATE / HANDOFF / ASK_CONTEXT / REFUSE / LIVE_CHECK",
            "never accept or repeat PII",
            "never use ARCHIVE for a current question",
        ],
        "context_fields": ["chunk_text", "title", "source_id", "locator",
                           "lifecycle", "freshness"],
    },
    "evaluation_set": {
        "core": 30, "supplementary": 6,
        "source": "Chunk_Corpus_RAG_AMIKOM_V1/00_manifest/"
                  "evaluation_chunk_coverage.csv",
        "retrieval_scored_subset": metrics["scored_subset"],
        "retrieval_scored_subset_rule": metrics["scored_subset_rule"],
    },
    "accepted_blockers_unchanged": ["G01", "G02", "G04", "CF002", "MR-A11-RELATIONS"],
    "stage_boundary": {
        "multi_agent": "NOT_EXECUTED",
        "coordinator_agent_final": "NOT_EXECUTED",
        "application_interface": "NOT_EXECUTED",
        "deployment": "NOT_EXECUTED",
        "fine_tuning": "NOT_EXECUTED",
    },
    "gates": {
        "retrieval_gate": evalj["gates"]["retrieval_gate"],
        "baseline_rag_gate": evalj["gates"]["baseline_rag_gate"],
        "ready_for_multi_agent": "NO",
    },
    "input_artifacts_sha256": {h["artifact"]: h["actual_sha256"]
                               for h in dbval["input_hash_checks"]},
    "environment": {
        "python_version": os.popen("python3 -V").read().strip(),
        "faiss_version": __import__("faiss").__version__,
        "sqlite_version": __import__("sqlite3").sqlite_version,
        "platform": "Linux cloud sandbox (network-restricted)",
    },
}
cfg_path = os.path.join(OUT, "Retrieval_Config_RAG_AMIKOM_V1.json")
blob = json.dumps(config, indent=2, ensure_ascii=False)
config["config_hash_algorithm"] = "SHA-256"
config["config_hash"] = hashlib.sha256(blob.encode()).hexdigest()
with open(cfg_path, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)
print("config written")
