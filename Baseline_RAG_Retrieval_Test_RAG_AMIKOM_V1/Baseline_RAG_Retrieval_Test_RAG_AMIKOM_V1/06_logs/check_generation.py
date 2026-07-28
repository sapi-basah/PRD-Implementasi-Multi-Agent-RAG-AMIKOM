"""Automated hallucination / citation / safety checks on the baseline RAG answers."""
from __future__ import annotations

import json
import os
import re
import sys

OUT = "/home/claude/work/out"
NUM_RE = re.compile(r"\b\d[\d.,/-]*\b")
PII_RE = [r"\b25XXXX\b", r"\bnim\s*\d", r"\b\d{8,}\b"]

STOP_NUM = {"1", "2", "3", "4", "5", "2025", "2026", "2027"}  # still checked, see below


def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def main():
    ans = load_jsonl(os.path.join(OUT, "Baseline_RAG_Answers.jsonl"))
    packs = {p["evaluation_id"]: p
             for p in json.load(open(os.path.join(OUT, "context_packs.json"),
                                     encoding="utf-8"))["packs"]}
    import sqlite3
    _con = sqlite3.connect(
        "file:/home/claude/work/vdb/Vector_Database_RAG_AMIKOM_V1/01_database/"
        "metadata.sqlite?mode=ro", uri=True)
    FULL_LOC = {r[0]: (r[1] or "") for r in _con.execute(
        "select chunk_id, locator from vector_records")}
    retr = {}
    for fn in ("Retrieval_Results_CORE.jsonl", "Retrieval_Results_SUPPLEMENTARY.jsonl"):
        for r in load_jsonl(os.path.join(OUT, fn)):
            retr[r["evaluation_id"]] = r

    report = []
    for a in ans:
        ev = a["evaluation_id"]
        p = packs[ev]
        r = retr[ev]
        ctx_ids = {c["chunk_id"] for c in p["context"]}
        # Grounding corpus = chunk text + the citable metadata that is part of the
        # assembled context (title, locator, academic_year, semester) + the user
        # question itself (echoing the asked term is not a new fact).
        ctx_text = " ".join(
            " ".join([c["chunk_text"], c["title"], FULL_LOC.get(c["chunk_id"], c["locator"]),
                      str(c["academic_year"]), str(c["semester"]),
                      c["lifecycle"], c["freshness"]])
            for c in p["context"]) + " " + p["question"]
        ctx_sources = {c["source_id"] for c in p["context"]}
        ctx_norm = re.sub(r"[.,]", "", ctx_text.lower())

        cit_ok = all(c["chunk_id"] in ctx_ids for c in a["citations"])
        cit_src_ok = all(c["source_id"] in ctx_sources for c in a["citations"])
        has_cit = len(a["citations"]) > 0

        # ungrounded numeric tokens in the answer
        ans_nums = [n for n in NUM_RE.findall(a["answer"])]
        ungrounded = []
        for n in ans_nums:
            n_clean = n.strip(".,")
            if not n_clean:
                continue
            if re.sub(r"[.,]", "", n_clean.lower()) in ctx_norm:
                continue
            # a range such as "35-36" or "20-27" is grounded when every numeric
            # component of it is present in the context (page ranges, date ranges)
            parts = [p for p in re.split(r"[-/]", n_clean) if p]
            if len(parts) > 1 and all(
                    re.search(r"\b0*" + re.escape(p) + r"\b", ctx_norm) for p in parts):
                continue
            ungrounded.append(n_clean)

        archive_used = [c["chunk_id"] for c in p["context"]
                        if c["lifecycle"] == "ARCHIVE"]
        archive_cited = [c["chunk_id"] for c in a["citations"]
                         if c["chunk_id"] in archive_used]
        current_question = r["applied_filter"]["mode"] == "CURRENT"
        archive_for_current = bool(archive_cited) and current_question

        pii_leak = [pat for pat in PII_RE if re.search(pat, a["answer"], re.I)]

        mode_ok = a["response_mode_applied"] == r["expected_response_mode"]

        report.append({
            "evaluation_id": ev,
            "test_set": a["test_set"],
            "expected_response_mode": r["expected_response_mode"],
            "response_mode_applied": a["response_mode_applied"],
            "response_mode_correct": mode_ok,
            "citation_present": has_cit,
            "citation_chunk_valid": cit_ok,
            "citation_source_valid": cit_src_ok,
            "citation_count": len(a["citations"]),
            "context_chunk_count": len(ctx_ids),
            "ungrounded_numeric_tokens": ungrounded,
            "archive_cited": archive_cited,
            "archive_used_for_current": archive_for_current,
            "pii_leak_patterns": pii_leak,
            "answer_len_words": len(a["answer"].split()),
            "abstain_reason": a.get("abstain_reason"),
            "handoff_target": a.get("handoff_target"),
            "live_check_note": a.get("live_check_note"),
        })

    with open(os.path.join(OUT, "generation_autochecks.json"), "w",
              encoding="utf-8") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)

    bad = [x for x in report if (not x["citation_chunk_valid"]
                                 or not x["citation_source_valid"]
                                 or x["ungrounded_numeric_tokens"]
                                 or x["archive_used_for_current"]
                                 or x["pii_leak_patterns"]
                                 or not x["response_mode_correct"])]
    print(f"checked {len(report)} answers; flagged {len(bad)}")
    for x in bad:
        print(" -", x["evaluation_id"],
              "mode_ok" if x["response_mode_correct"] else "MODE_MISMATCH",
              "cit_ok" if x["citation_chunk_valid"] and x["citation_source_valid"]
              else "CITATION_MISMATCH",
              ("UNGROUNDED:" + ",".join(x["ungrounded_numeric_tokens"]))
              if x["ungrounded_numeric_tokens"] else "",
              "ARCHIVE_FOR_CURRENT" if x["archive_used_for_current"] else "",
              "PII" if x["pii_leak_patterns"] else "")


if __name__ == "__main__":
    main()
