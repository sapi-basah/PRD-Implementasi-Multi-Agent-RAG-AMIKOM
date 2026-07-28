"""Baseline retriever.

Order of operations is fixed and never inverted:

    control check  ->  metadata filter (SQLite)  ->  scoring on the candidate set
                   ->  top-k

Scoring backend in this run is BM25 Okapi over `title + chunk_text`
(`FALLBACK_LEXICAL_BM25_V1`) because the mandated E5 query encoder is blocked
(see encoder.py). The FAISS index is still opened and smoke-tested, but no
query-vector search was executed.

IDF statistics are computed once over the whole 306-record indexed corpus, which
is a static corpus property and does not leak namespace membership: the ranked
set is strictly the SQLite candidate set.
"""
from __future__ import annotations

import math
import re
import time
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

BACKEND = "FALLBACK_LEXICAL_BM25_V1"
K1 = 1.5
B = 0.75

STOPWORDS = {
    "yang", "dan", "di", "ke", "dari", "untuk", "pada", "dengan", "atau", "adalah",
    "ini", "itu", "apa", "apakah", "bagaimana", "berapa", "kapan", "dimana", "mana",
    "saya", "anda", "kita", "kami", "bisa", "dapat", "akan", "sudah", "masih",
    "tolong", "mohon", "ada", "juga", "oleh", "sebagai", "dalam", "agar", "jika",
    "the", "a", "an", "of", "to", "is", "are", "sebuah", "para", "seperti", "bagi",
}

TOKEN_RE = re.compile(r"[a-z0-9]+", re.I)


def tokenize(text: str) -> List[str]:
    toks = [t.lower() for t in TOKEN_RE.findall(text or "")]
    out = []
    for t in toks:
        if len(t) < 2 and not t.isdigit():
            continue
        if t in STOPWORDS:
            continue
        out.append(t)
    return out


@dataclass
class Hit:
    vector_index: int
    chunk_id: str
    score: float
    rank: int
    normalized_score: float


class BM25Index:
    def __init__(self, records):
        self.records = {r.vector_index: r for r in records}
        self.docs: Dict[int, Counter] = {}
        self.len: Dict[int, int] = {}
        df = Counter()
        for r in records:
            toks = tokenize(r.title) + tokenize(r.chunk_text)
            c = Counter(toks)
            self.docs[r.vector_index] = c
            self.len[r.vector_index] = len(toks)
            for t in c:
                df[t] += 1
        self.N = len(records)
        self.avgdl = sum(self.len.values()) / max(1, self.N)
        self.idf = {
            t: math.log(1 + (self.N - n + 0.5) / (n + 0.5)) for t, n in df.items()
        }

    def score_candidates(
        self, query: str, candidates: List[int]
    ) -> List[Tuple[int, float]]:
        q = tokenize(query)
        out = []
        for vi in candidates:
            c = self.docs[vi]
            dl = self.len[vi]
            s = 0.0
            for t in q:
                f = c.get(t)
                if not f:
                    continue
                idf = self.idf.get(t, 0.0)
                s += idf * (f * (K1 + 1)) / (f + K1 * (1 - B + B * dl / self.avgdl))
            if s > 0:
                out.append((vi, s))
        out.sort(key=lambda x: (-x[1], x[0]))
        return out


def retrieve(
    index: BM25Index,
    query_text: str,
    candidates: List[int],
    k: int,
) -> Tuple[List[Hit], float]:
    t0 = time.perf_counter()
    scored = index.score_candidates(query_text, candidates)
    top = scored[:k]
    mx = top[0][1] if top else 1.0
    hits = [
        Hit(
            vector_index=vi,
            chunk_id=index.records[vi].chunk_id,
            score=round(s, 6),
            rank=i + 1,
            normalized_score=round(s / mx, 6) if mx else 0.0,
        )
        for i, (vi, s) in enumerate(top)
    ]
    latency_ms = (time.perf_counter() - t0) * 1000.0
    return hits, latency_ms
