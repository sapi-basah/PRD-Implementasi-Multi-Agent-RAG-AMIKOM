"""Query encoder.

MANDATED ENCODER (Section 3 of the stage brief)
    model     : Xenova/multilingual-e5-small
    revision  : 761b726dd34fb83930e26aab4e9ac3899aa1fa78
    prefix    : "query: "
    pooling   : mean, then L2 normalisation, float32, dim 384

STATUS IN THIS RUN: NOT_EXECUTED / BLOCKED.
The execution sandbox blocks huggingface.co (HTTP CONNECT tunnel -> 403), and the
model weights are not present in any of the immutable input artefacts, so the
mandated encoder could not be instantiated and no query vector could be produced.

Consequence: FAISS inner-product search over the 306 stored vectors could not be
executed for the evaluation queries. A deterministic lexical fallback retriever
(BM25 Okapi, see retriever.py) is used instead so that the control layer, the
metadata filter, the metric harness and the baseline RAG pipeline can still be
exercised end to end. Every affected artefact is labelled
`retriever_backend = FALLBACK_LEXICAL_BM25_V1`.
"""
from __future__ import annotations

MANDATED = {
    "model_name": "Xenova/multilingual-e5-small",
    "model_revision": "761b726dd34fb83930e26aab4e9ac3899aa1fa78",
    "tokenizer": "XLMRobertaTokenizer — Xenova/multilingual-e5-small",
    "query_prefix": "query: ",
    "document_prefix": "passage: ",
    "pooling_strategy": "mean",
    "normalize_embeddings": True,
    "embedding_dimension": 384,
    "embedding_dtype": "float32",
}

BLOCK_REASON = (
    "huggingface.co unreachable from the execution sandbox "
    "(proxy CONNECT tunnel failed, HTTP 403); model artefacts "
    "config.json / tokenizer.json / onnx/model_int8.onnx are not bundled in any "
    "immutable input package."
)


def format_query(question: str) -> str:
    """E5 asymmetric formatting. `passage:` is never used for questions."""
    return MANDATED["query_prefix"] + question.strip()


def encode_query(question: str):
    """Would return a (384,) float32 L2-normalised vector. Blocked in this run."""
    raise RuntimeError("QUERY_EMBEDDING_BLOCKED: " + BLOCK_REASON)


def query_vector_status() -> dict:
    return {
        "status": "NOT_EXECUTED",
        "reason": BLOCK_REASON,
        "formatted_prefix_applied": True,
        "dimension": None,
        "dtype": None,
        "norm": None,
        "nan_or_inf": None,
    }
