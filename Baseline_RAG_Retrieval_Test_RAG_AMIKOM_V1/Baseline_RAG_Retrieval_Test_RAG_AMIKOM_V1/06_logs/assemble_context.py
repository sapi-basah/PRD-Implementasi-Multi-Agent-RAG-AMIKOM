"""Context assembly for the baseline RAG generator (single generator, no agents)."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ragx import control, store  # noqa: E402

OUT = "/home/claude/work/out"
BASELINE_TOP_K = int(os.environ.get("BASELINE_TOP_K", "5"))

GENERATOR_PROMPT = """SISTEM: Baseline RAG AMIKOM V1 - single generator, tanpa multi-agent.

ATURAN WAJIB
1. Jawab HANYA dari RETRIEVED CONTEXT di bawah. Dilarang menambah fakta, tanggal,
   angka, biaya, atau nama layanan yang tidak tertulis di context.
2. Setiap klaim faktual wajib disertai sitasi [source_id | locator].
3. Bila context tidak cukup, katakan informasi tidak ditemukan pada sumber
   terverifikasi. Jangan menebak.
4. Patuhi CONTROL DIRECTIVE: ABSTAIN, ESCALATE, HANDOFF, ASK_CONTEXT, REFUSE, dan
   LIVE_CHECK mengalahkan keinginan untuk menjawab.
5. Jangan meminta, menerima, mengulang, atau menyimpan data pribadi (NIM, KTP, KK,
   akta, nomor kontak, transkrip, tagihan).
6. Record berlifecycle ARCHIVE tidak boleh dipakai menjawab pertanyaan current;
   record ACTIVE_DYNAMIC yang melewati TTL wajib ditandai perlu live check.
7. CONTROL DIRECTIVE bukan pengetahuan faktual; jangan mengutipnya sebagai fakta
   akademik, gunakan hanya sebagai dasar keputusan mode jawaban.
8. Bila sumber resmi berkonflik (CF002), tampilkan konflik dan eskalasi; jangan
   memilih salah satu nilai.
"""


def control_directive(d, ctl_records):
    lines = [f"response_mode = {d.response_mode}",
             f"control_triggered = {', '.join(d.control_triggered) or 'NONE'}",
             f"guardrail_action = {d.guardrail_action}",
             f"handoff_required = {d.handoff_required} -> {d.handoff_target}",
             f"authentication_required = {d.authentication_required}",
             f"live_check_required = {d.live_check_required}"]
    if d.partial_abstain:
        lines.append("partial_abstain = " + "; ".join(d.partial_abstain))
    if d.source_constraints:
        lines.append("source_constraints = " + "; ".join(d.source_constraints))
    ids = set(d.control_triggered)
    for kind, recs in ctl_records.items():
        for r in recs:
            cid = r.get("control_id", "")
            conf = r.get("conflict_id", "")
            if (cid and cid in ids) or (conf and conf in ids):
                lines.append(
                    f"[{kind} {cid or conf}] {r['title']} :: {r['chunk_text']} "
                    f"(locator: {r.get('locator_text', 'NOT_APPLICABLE')})")
    return "\n".join(lines)


def main():
    con = store.open_db()
    recs = {r.chunk_id: r for r in store.load_all(con)}
    ctl = store.load_control_registry()
    rows = []
    for fn in ("Retrieval_Results_CORE.jsonl", "Retrieval_Results_SUPPLEMENTARY.jsonl"):
        with open(os.path.join(OUT, fn), encoding="utf-8") as f:
            rows += [json.loads(l) for l in f if l.strip()]

    packs = []
    for r in rows:
        d = control.route(r["question"])
        ctx = []
        for cid, score in zip(r["per_k"][str(BASELINE_TOP_K)]["retrieved_chunk_ids"],
                              r["per_k"][str(BASELINE_TOP_K)]["similarity_scores"]):
            rec = recs[cid]
            fc = control.freshness_check(rec)
            ctx.append({
                "chunk_id": cid,
                "score": score,
                "source_id": rec.source_id,
                "title": rec.title,
                "locator": rec.locator.replace("<!-- locator: ", "")[:190],
                "lifecycle": rec.lifecycle_status,
                "freshness": rec.freshness_status,
                "freshness_eval": fc,
                "academic_year": rec.academic_year,
                "semester": rec.semester,
                "chunk_text": rec.chunk_text,
            })
        packs.append({
            "evaluation_id": r["evaluation_id"],
            "test_set": r["test_set"],
            "question": r["question"],
            "control_directive": control_directive(d, ctl),
            "context": ctx,
        })
    with open(os.path.join(OUT, "context_packs.json"), "w", encoding="utf-8") as f:
        json.dump({"baseline_top_k": BASELINE_TOP_K,
                   "generator_prompt": GENERATOR_PROMPT,
                   "packs": packs}, f, ensure_ascii=False, indent=1)
    print("packs", len(packs))


if __name__ == "__main__":
    main()
