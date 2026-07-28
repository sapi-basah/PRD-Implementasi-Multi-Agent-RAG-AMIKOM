"""Input validation + FAISS functional smoke test (no query vector available)."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sqlite3

import faiss
import numpy as np

WIB = dt.timezone(dt.timedelta(hours=7))
BASE = "/home/claude/work/vdb/Vector_Database_RAG_AMIKOM_V1"
INP = "/home/claude/work/inputs"
OUT = "/home/claude/work/out"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    fpv = json.load(open(os.path.join(INP, "afb3f4c8-final_package_validation.json"),
                         encoding="utf-8"))
    req = fpv["required_outputs"]
    files = {
        "Vector_Database_RAG_AMIKOM_V1.zip":
            "06d63ec8-Vector_Database_RAG_AMIKOM_V1.zip",
        "Manifest_Vector_Database_RAG_AMIKOM_V1.xlsx":
            "f2fff075-Manifest_Vector_Database_RAG_AMIKOM_V1.xlsx",
        "Laporan_Vector_Database_Indexing_RAG_AMIKOM_V1.pdf":
            "5fad65a4-Laporan_Vector_Database_Indexing_RAG_AMIKOM_V1.pdf",
        "README_Vector_Database_RAG_AMIKOM_V1.md":
            "7df8ff59-README_Vector_Database_RAG_AMIKOM_V1.md",
        "Vector_Database_Config_RAG_AMIKOM_V1.json":
            "b190dbca-Vector_Database_Config_RAG_AMIKOM_V1.json",
    }
    hashes = []
    for name, fn in files.items():
        actual = sha256(os.path.join(INP, fn))
        hashes.append({"artifact": name, "expected_sha256": req[name]["sha256"],
                       "actual_sha256": actual,
                       "status": "PASS" if actual == req[name]["sha256"] else "FAIL"})
    jl = "/home/claude/work/chunks/Chunk_Corpus_RAG_AMIKOM_V1/Chunk_Corpus_RAG_AMIKOM_V1.jsonl"
    a = sha256(jl)
    e = "9bc4147b2872db0dba4ff46b0d1050662f61975b672555212ddabdf5b68e174e"
    hashes.append({"artifact": "Chunk_Corpus_RAG_AMIKOM_V1.jsonl",
                   "expected_sha256": e, "actual_sha256": a,
                   "status": "PASS" if a == e else "FAIL"})

    idx = faiss.read_index(os.path.join(BASE, "01_database", "faiss.index"))
    con = sqlite3.connect(
        f"file:{os.path.join(BASE, '01_database', 'metadata.sqlite')}?mode=ro", uri=True)
    n_sql = con.execute("select count(*) from vector_records").fetchone()[0]
    vmin, vmax = con.execute(
        "select min(vector_index), max(vector_index) from vector_records").fetchone()

    # functional smoke test: reconstruct a stored vector and search with it
    v0 = idx.reconstruct(0).reshape(1, -1).astype("float32")
    D, I = idx.search(v0, 3)
    norm = float(np.linalg.norm(v0))
    rt = json.load(open(os.path.join(BASE, "05_qa", "reload_test.json"),
                        encoding="utf-8"))
    out = {
        "validated_at_wib": dt.datetime.now(WIB).isoformat(),
        "stage": "BASELINE_RAG_RETRIEVAL_TESTING",
        "input_hash_checks": hashes,
        "input_hash_status": "PASS" if all(h["status"] == "PASS" for h in hashes)
                             else "FAIL",
        "faiss": {
            "ntotal": int(idx.ntotal), "dimension": int(idx.d),
            "index_class": type(idx).__name__,
            "file_sha256": sha256(os.path.join(BASE, "01_database", "faiss.index")),
            "file_sha256_matches_previous_stage":
                sha256(os.path.join(BASE, "01_database", "faiss.index"))
                == rt["faiss_index_sha256"],
        },
        "sqlite": {
            "record_count": n_sql, "vector_index_range": [vmin, vmax],
            "file_sha256": sha256(os.path.join(BASE, "01_database", "metadata.sqlite")),
            "file_sha256_matches_previous_stage":
                sha256(os.path.join(BASE, "01_database", "metadata.sqlite"))
                == rt["metadata_sqlite_sha256"],
        },
        "faiss_functional_smoke_test": {
            "method": "reconstruct(vector_index=0) then search(k=3) on the same index",
            "reconstructed_norm": round(norm, 6),
            "self_match_index": int(I[0][0]),
            "self_match_score": round(float(D[0][0]), 6),
            "top3_indexes": [int(x) for x in I[0]],
            "top3_scores": [round(float(x), 6) for x in D[0]],
            "status": "PASS" if int(I[0][0]) == 0 and abs(float(D[0][0]) - 1.0) < 1e-3
                      else "FAIL",
            "note": "Proves the index is functional and cosine-normalised. It does NOT "
                    "prove query-side retrieval, which needs the mandated E5 encoder.",
        },
        "query_encoder": {
            "mandated_model": "Xenova/multilingual-e5-small",
            "mandated_revision": "761b726dd34fb83930e26aab4e9ac3899aa1fa78",
            "status": "NOT_EXECUTED",
            "reason": "huggingface.co blocked by the execution sandbox proxy (403); "
                      "model artefacts are not bundled in any immutable input package.",
            "query_vectors_produced": 0,
        },
        "vector_database_gate_previous_stage": fpv["vector_database_gate"],
        "artifacts_unmodified": True,
    }
    with open(os.path.join(OUT, "database_validation.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(json.dumps({k: out[k] for k in
                      ("input_hash_status", "faiss", "sqlite",
                       "faiss_functional_smoke_test")}, indent=1))


if __name__ == "__main__":
    main()
