"""Vector store + metadata store access layer for RAG AMIKOM V1 retrieval testing.

Read-only. Never mutates the upstream Vector Database package.
"""
from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

BASE = os.environ.get(
    "RAG_VDB_BASE", "/home/claude/work/vdb/Vector_Database_RAG_AMIKOM_V1"
)
CHUNK_BASE = os.environ.get(
    "RAG_CHUNK_BASE", "/home/claude/work/chunks/Chunk_Corpus_RAG_AMIKOM_V1"
)

FAISS_PATH = os.path.join(BASE, "01_database", "faiss.index")
SQLITE_PATH = os.path.join(BASE, "01_database", "metadata.sqlite")

ACTIVE_NAMESPACES = [
    "active_academic",
    "active_schedule",
    "active_administration",
    "active_dynamic_schedule",
]
ARCHIVE_NAMESPACE = "archive_schedule"


@dataclass
class Record:
    vector_index: int
    vector_id: str
    chunk_id: str
    chunk_text: str
    source_id: str
    document_id: str
    title: str
    locator: str
    agent_namespace: str
    retrieval_namespace: str
    lifecycle_status: str
    academic_year: str
    semester: str
    freshness_status: str
    ttl_days: Any
    live_check_required: int
    snapshot_at_wib: str
    historical_only: int
    active_retrieval_allowed: int
    source_priority: str
    meta: Dict[str, Any] = field(default_factory=dict)


def open_db() -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


_COLS = (
    "vector_index, vector_id, chunk_id, chunk_text, source_id, document_id, title, "
    "locator, agent_namespace, retrieval_namespace, lifecycle_status, academic_year, "
    "semester, freshness_status, ttl_days, live_check_required, snapshot_at_wib, "
    "historical_only, active_retrieval_allowed, source_priority, metadata_json"
)


def _row_to_record(r: sqlite3.Row) -> Record:
    d = dict(r)
    meta = {}
    try:
        meta = json.loads(d.pop("metadata_json") or "{}")
    except Exception:
        d.pop("metadata_json", None)
    return Record(meta=meta, **d)


def load_all(con: sqlite3.Connection) -> List[Record]:
    return [_row_to_record(r) for r in con.execute(f"select {_COLS} from vector_records")]


def candidate_indexes(
    con: sqlite3.Connection,
    namespaces: List[str],
    mode: str = "CURRENT",
) -> List[int]:
    """METADATA FILTER BEFORE RANKING.

    Returns the candidate `vector_index` list straight from SQLite. Ranking is only
    ever computed on this candidate set - never global top-k followed by discard.
    """
    if not namespaces:
        return []
    ph = ",".join("?" * len(namespaces))
    if mode == "CURRENT":
        sql = (
            f"select vector_index from vector_records "
            f"where active_retrieval_allowed = 1 and historical_only = 0 "
            f"and retrieval_namespace in ({ph}) order by vector_index"
        )
    elif mode == "HISTORICAL":
        sql = (
            f"select vector_index from vector_records "
            f"where historical_only = 1 and lifecycle_status = 'ARCHIVE' "
            f"and retrieval_namespace in ({ph}) order by vector_index"
        )
    else:
        raise ValueError(mode)
    return [int(r[0]) for r in con.execute(sql, namespaces)]


def records_by_index(con: sqlite3.Connection, idxs: List[int]) -> Dict[int, Record]:
    if not idxs:
        return {}
    out: Dict[int, Record] = {}
    CH = 400
    for i in range(0, len(idxs), CH):
        part = idxs[i : i + CH]
        ph = ",".join("?" * len(part))
        for r in con.execute(
            f"select {_COLS} from vector_records where vector_index in ({ph})", part
        ):
            rec = _row_to_record(r)
            out[rec.vector_index] = rec
    return out


def load_control_registry() -> Dict[str, List[Dict[str, Any]]]:
    """CONTROL / CONFLICT / BLOCKED records are loaded from the Chunk Corpus only.

    They are deliberately NOT in the vector database (FV11) and must never be
    treated as vector knowledge.
    """
    out: Dict[str, List[Dict[str, Any]]] = {}
    files = {
        "CONTROL": "chunk_control.jsonl",
        "CONFLICT": "chunk_conflict_verifier.jsonl",
        "BLOCKED": "chunk_blocked_verifier.jsonl",
    }
    for kind, fn in files.items():
        path = os.path.join(CHUNK_BASE, fn)
        recs = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    recs.append(json.loads(line))
        out[kind] = recs
    return out
