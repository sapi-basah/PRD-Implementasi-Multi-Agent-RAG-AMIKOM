"""Laporan_Baseline_RAG_Retrieval_Test_RAG_AMIKOM_V1.pdf"""
from __future__ import annotations

import datetime as dt
import json
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

WIB = dt.timezone(dt.timedelta(hours=7))
OUT = "/home/claude/work/out"
NOW = dt.datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S WIB")


def jload(p):
    return json.load(open(os.path.join(OUT, p), encoding="utf-8"))


def jlload(p):
    return [json.loads(l) for l in open(os.path.join(OUT, p), encoding="utf-8")
            if l.strip()]


metrics = jload("retrieval_metrics.json")
evalj = jload("baseline_rag_evaluation.json")
dbval = jload("database_validation.json")
core = jlload("Retrieval_Results_CORE.jsonl")
supp = jlload("Retrieval_Results_SUPPLEMENTARY.jsonl")
allr = core + supp
grades = {r["evaluation_id"]: r for r in evalj["rows"]}

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName="Helvetica-Bold",
                    fontSize=14, spaceAfter=8, textColor=colors.HexColor("#1F3864"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="Helvetica-Bold",
                    fontSize=11.5, spaceBefore=10, spaceAfter=5,
                    textColor=colors.HexColor("#1F3864"))
BODY = ParagraphStyle("BODY", parent=ss["BodyText"], fontName="Helvetica",
                      fontSize=9, leading=12.5, alignment=TA_JUSTIFY, spaceAfter=5)
SMALL = ParagraphStyle("SMALL", parent=BODY, fontSize=7.5, leading=9.5)
CELL = ParagraphStyle("CELL", parent=BODY, fontSize=7.5, leading=9,
                      alignment=0, spaceAfter=0)
CELLB = ParagraphStyle("CELLB", parent=CELL, fontName="Helvetica-Bold")
WARN = ParagraphStyle("WARN", parent=BODY, textColor=colors.HexColor("#9C0006"),
                      fontName="Helvetica-Bold")

TS = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BFBFBF")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F5FA")]),
    ("LEFTPADDING", (0, 0), (-1, -1), 3),
    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ("TOPPADDING", (0, 0), (-1, -1), 2),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
])


def tbl(headers, rows, widths):
    data = [[Paragraph(str(h), CELLB) for h in headers]]
    for r in rows:
        data.append([Paragraph(str(c), CELL) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TS)
    return t


story = []
A = story.append

A(Paragraph("Laporan Baseline RAG dan Retrieval Testing", H1))
A(Paragraph("Corpus RAG AMIKOM — Paket Baseline_RAG_Retrieval_Test_RAG_AMIKOM_V1", BODY))
A(Paragraph(f"Disusun: {NOW} &nbsp;|&nbsp; Scope Status: FROZEN &nbsp;|&nbsp; "
            f"Vector Database Gate: PASS", BODY))
A(Spacer(1, 6))

A(Paragraph("Ringkasan Eksekutif", H2))
A(Paragraph(
    "Tahap ini membangun retriever baseline di atas Vector Database RAG AMIKOM V1 "
    "(FAISS IndexIDMap2(IndexFlatIP) 306 vector, dimensi 384, ditambah metadata "
    "SQLite 306 record), menjalankan lapisan kontrol dan filter metadata sebelum "
    "ranking, menguji 30 kasus CORE dan 6 kasus SUPPLEMENTARY pada k = 1, 3, 5, 10, "
    "menetapkan baseline top-k, lalu menjalankan satu baseline RAG generator tunggal "
    "beserta evaluasi accuracy, effectiveness, efficiency, explainability, dan "
    "hallucination. Seluruh artefak tahap sebelumnya diverifikasi SHA-256 dan tidak "
    "dimodifikasi.", BODY))
A(Paragraph(
    "BATASAN UTAMA: query encoder yang dimandatkan (Xenova/multilingual-e5-small "
    "revisi 761b726dd34fb83930e26aab4e9ac3899aa1fa78) TIDAK dapat dijalankan karena "
    "huggingface.co diblokir oleh proxy lingkungan eksekusi (CONNECT 403) dan "
    "artefak model tidak dibundel pada paket input mana pun. Akibatnya tidak ada "
    "query vector yang dihasilkan dan FAISS search tidak dijalankan untuk 36 query "
    "evaluasi. Atas persetujuan eksplisit pemilik pekerjaan, tahap ini dilanjutkan "
    "memakai retriever pengganti berbasis leksikal BM25 Okapi "
    "(FALLBACK_LEXICAL_BM25_V1) sehingga lapisan kontrol, filter, metrik, dan "
    "generasi tetap teruji ujung ke ujung. Konsekuensinya angka Hit@k, Recall@k, "
    "Precision@k, dan MRR pada laporan ini TIDAK mewakili performa vector search E5 "
    "dan baseline top-k bersifat sementara.", WARN))

A(Paragraph("Status Akhir", H2))
g = evalj["gates"]
m5 = metrics["per_k"]["5"]
iso = metrics["isolation_and_control"]
A(tbl(["Item", "Nilai"], [
    ["Scope Status", "FROZEN"],
    ["Vector Database Gate", "PASS (diverifikasi ulang: hash, ntotal 306, dim 384)"],
    ["Retrieval Testing", "PARTIALLY_COMPLETE"],
    ["Baseline Top-k", "5 (sementara, backend leksikal)"],
    ["Retrieval Metrics",
     f'Hit@1 {metrics["per_k"]["1"]["hit_at_k"]} | Hit@3 {metrics["per_k"]["3"]["hit_at_k"]} | '
     f'Hit@5 {m5["hit_at_k"]} | Hit@10 {metrics["per_k"]["10"]["hit_at_k"]} | '
     f'Recall@5 {m5["recall_at_k"]} | Precision@5 {m5["precision_at_k"]} | '
     f'MRR@10 {metrics["per_k"]["10"]["mrr_at_k"]}'],
    ["Control Accuracy", f'{iso["control_decision_accuracy"]} (36/36)'],
    ["Archive Leakage", str(iso["archive_leakage_count"])],
    ["Baseline RAG", "COMPLETE"],
    ["Retrieval Gate", g["retrieval_gate"]],
    ["Baseline RAG Gate", g["baseline_rag_gate"]],
    ["Ready for Multi-Agent Implementation", "NO"],
    ["Multi-Agent Executed", "NO"],
], [150, 340]))

A(PageBreak())
A(Paragraph("1. Validasi Input dan Database", H2))
A(Paragraph(
    f'Enam artefak input diverifikasi ulang dengan SHA-256 terhadap '
    f'final_package_validation.json dan seluruhnya identik '
    f'({dbval["input_hash_status"]}). FAISS terbaca dengan ntotal '
    f'{dbval["faiss"]["ntotal"]} dan dimensi {dbval["faiss"]["dimension"]}; SQLite '
    f'memuat {dbval["sqlite"]["record_count"]} record dengan vector_index '
    f'{dbval["sqlite"]["vector_index_range"][0]}-{dbval["sqlite"]["vector_index_range"][1]}. '
    f'Hash file faiss.index dan metadata.sqlite identik dengan reload_test.json tahap '
    f'sebelumnya, sehingga artefak terbukti tidak berubah. Database dibuka read-only '
    f'(SQLite URI mode=ro).', BODY))
sm = dbval["faiss_functional_smoke_test"]
A(Paragraph(
    f'Uji fungsional FAISS dilakukan tanpa query vector: vektor pada index 0 '
    f'direkonstruksi lalu dicarikan kembali. Hasilnya self-match pada index '
    f'{sm["self_match_index"]} dengan skor {sm["self_match_score"]} dan norm '
    f'{sm["reconstructed_norm"]}, membuktikan index berfungsi dan ternormalisasi '
    f'kosinus. Uji ini TIDAK membuktikan retrieval sisi query.', BODY))

A(Paragraph("2. Query Embedding", H2))
A(tbl(["Aspek", "Spesifikasi wajib", "Status eksekusi"], [
    ["Model", "Xenova/multilingual-e5-small", "NOT_EXECUTED"],
    ["Revision", "761b726dd34fb83930e26aab4e9ac3899aa1fa78", "NOT_EXECUTED"],
    ["Tokenizer", "XLMRobertaTokenizer resmi model", "NOT_EXECUTED"],
    ["Prefix query", "query: [pertanyaan]", "Dibentuk untuk 36 query dan disimpan "
                                            "pada field formatted_query"],
    ["Prefix passage", "tidak boleh dipakai untuk pertanyaan", "Dipatuhi"],
    ["Pooling", "mean", "NOT_EXECUTED"],
    ["Normalisasi", "L2", "NOT_EXECUTED"],
    ["Dimensi / dtype", "384 / float32", "Tidak ada vector dihasilkan"],
    ["Validasi NaN/Inf/zero/norm", "wajib", "Tidak dapat dijalankan"],
], [70, 200, 220]))

A(Paragraph("3. Control dan Routing Sebelum Retrieval", H2))
A(Paragraph(
    "Record CONTROL (10), CONFLICT (2), dan BLOCKED (1) dimuat terpisah dari Chunk "
    "Corpus dan tidak pernah diperlakukan sebagai vector knowledge — ketiganya memang "
    "tidak diindeks (dikonfirmasi FV11). Lapisan kontrol dijalankan sebelum filter "
    "dan sebelum ranking, dengan urutan prioritas: privacy/PII (INT07), out-of-scope "
    "(beasiswa, keuangan, karier, magang), sumber karantina (INT05), archive-sebagai-"
    "current (INT05), konflik terbuka CF002 (INT06), rute temporal G02/G01, "
    "penyetaraan CF001, dan relasi ambigu MR-A11-RELATIONS. Ketika G02 aktif, "
    "namespace jadwal dibuang dari himpunan kandidat sehingga tidak ada tanggal yang "
    "dapat bocor ke context.", BODY))
rows = []
for r in allr:
    if r["control_triggered"]:
        rows.append([r["evaluation_id"], "|".join(r["control_triggered"]),
                     r["expected_response_mode"], r["predicted_response_mode"],
                     "OK" if r["expected_response_mode"] ==
                     r["predicted_response_mode"] else "MISMATCH",
                     r["retrieval_status"]])
A(tbl(["ID", "control_triggered", "mode diharapkan", "mode diputuskan", "hasil",
       "retrieval_status"], rows, [50, 150, 65, 65, 45, 105]))

A(PageBreak())
A(Paragraph("4. Metadata Filter Sebelum Ranking", H2))
A(Paragraph(
    "Kandidat vector_index ditentukan lebih dulu melalui SQLite, baru skor dihitung "
    "pada kandidat tersebut. Tidak ada global top-k yang kemudian dibuang. Predikat "
    "current: active_retrieval_allowed=1 AND historical_only=0 AND retrieval_namespace "
    "IN (namespace aktif hasil routing). Predikat historis: historical_only=1 AND "
    "lifecycle_status='ARCHIVE' AND retrieval_namespace='archive_schedule'. Mode MIXED "
    "dipakai untuk pertanyaan multi-intent yang menggabungkan sub-intent historis dan "
    "prosedural current.", BODY))
A(Paragraph(
    "Hasil: namespace/filter accuracy 1.00 pada 36 query, isolasi historis 1.00 pada "
    "3 query archive, dan archive leakage 0 pada seluruh query current bahkan pada "
    "k=10. Sepuluh record ACTIVE_DYNAMIC (A03, ttl 1 hari, snapshot 2026-07-24) "
    "dinilai kedaluwarsa pada waktu eksekusi 2026-07-27 sehingga diberi "
    "response_mode LIVE_CHECK_OR_ABSTAIN.", BODY))

A(Paragraph("5. Hasil Retrieval dan Perbandingan Top-k", H2))
A(Paragraph(
    "Metrik retrieval dihitung pada subset ber-skor: 20 query yang memang menuntut "
    "retrieval faktual (expected_response_mode ANSWER atau ASK_CONTEXT) dan memiliki "
    "minimal satu gold chunk di dalam database. Enam belas query sisanya adalah kasus "
    "kontrol (ABSTAIN/ESCALATE/REFUSE) yang gold chunk-nya berupa record "
    "CONTROL/CONFLICT/BLOCKED di luar vector database; kasus tersebut dinilai melalui "
    "control decision accuracy, bukan Hit@k.", BODY))
rows = []
for k in ("1", "3", "5", "10"):
    m = metrics["per_k"][k]
    rows.append([k, m["hit_at_k"], m["recall_at_k"], m["precision_at_k"],
                 m["mrr_at_k"], m["source_accuracy"], m["avg_irrelevant_chunks"],
                 m["avg_context_tokens_est"], m["latency"]["p95_ms"],
                 "DIPILIH" if k == "5" else ""])
A(tbl(["k", "Hit@k", "Recall@k", "Precision@k", "MRR@k", "Source acc",
       "Chunk tak relevan", "Token context (est.)", "Latency P95 (ms)", "Keputusan"],
      rows, [22, 42, 48, 52, 42, 50, 62, 70, 62, 50]))
A(Paragraph(
    "Baseline top-k ditetapkan 5. Hit@5 sama dengan Hit@3 (0.80) tetapi Recall@5 "
    "lebih tinggi (0.73 vs 0.65) karena banyak gold prosedural terdiri dari 3-6 chunk "
    "(B03, B04, B05, B06, B07, B01+B02). Menaikkan k ke 10 memang mengangkat Hit ke "
    "0.95 dan Recall ke 0.91, tetapi menambah rata-rata 6.4 chunk tidak relevan per "
    "query (context 616 token) sehingga memperbesar risiko unsupported generation, "
    "sementara MRR hampir tidak berubah (0.725 ke 0.744). Latency tidak menjadi "
    "pembeda pada backend leksikal. Nilai ini dicatat sebagai baseline_top_k, bukan "
    "final production top-k, dan wajib ditinjau ulang setelah encoder E5 tersedia "
    "serta pada tahap multi-agent evaluation.", BODY))

A(PageBreak())
A(Paragraph("6. Baseline RAG", H2))
A(Paragraph(
    "Pipeline yang dijalankan: query &rarr; control check &rarr; metadata filter "
    "&rarr; (query embedding: NOT_EXECUTED) &rarr; retrieval &rarr; context assembly "
    "&rarr; satu generator LLM &rarr; jawaban + citation. Generator adalah satu model "
    "tunggal (claude-opus-5) tanpa coordinator, verifier, atau agen lain. Context "
    "memuat chunk_text, title, source_id, locator, lifecycle, dan freshness; control "
    "directive disertakan terpisah sebagai dasar keputusan mode, bukan sebagai fakta.",
    BODY))
acc = evalj["accuracy"]
hal = evalj["hallucination"]
exp = evalj["explainability"]
eff = evalj["efficiency"]
A(tbl(["Dimensi", "Hasil"], [
    ["Accuracy", f'response mode 36/36 ({acc["response_mode_accuracy"]}); factual PASS '
                 f'{acc["factual_pass_rate_scored_subset"]}, PARTIAL '
                 f'{acc["factual_partial_rate_scored_subset"]}, FAIL '
                 f'{acc["factual_fail_rate_scored_subset"]} pada 20 query ber-skor'],
    ["Effectiveness", f'{evalj["grade_distribution"].get("PASS", 0)} PASS, '
                      f'{evalj["grade_distribution"].get("PARTIAL", 0)} PARTIAL, '
                      f'{evalj["grade_distribution"].get("ABSTAIN_CORRECT", 0)} '
                      f'ABSTAIN_CORRECT, '
                      f'{evalj["grade_distribution"].get("HANDOFF_CORRECT", 0)} '
                      f'HANDOFF_CORRECT, '
                      f'{evalj["grade_distribution"].get("OUT_OF_SCOPE_CORRECT", 0)} '
                      f'OUT_OF_SCOPE_CORRECT, 0 FAIL'],
    ["Efficiency", f'retrieval latency mean {eff["retrieval_latency"]["mean_ms"]} ms, '
                   f'median {eff["retrieval_latency"]["median_ms"]} ms, P95 '
                   f'{eff["retrieval_latency"]["p95_ms"]} ms; context rata-rata '
                   f'{eff["avg_context_chunks"]} chunk / '
                   f'{eff["avg_context_tokens_est"]} token; generation latency '
                   f'NOT_MEASURED'],
    ["Explainability", f'{exp["answers_with_citation"]} jawaban bersitasi, '
                       f'{exp["answers_without_citation_by_control"]} jawaban jalur '
                       f'kontrol tanpa sitasi (memang tanpa retrieval faktual); '
                       f'seluruh citation dapat ditelusuri ke chunk_id, source_id, '
                       f'dan locator; alasan abstain/handoff tercatat pada '
                       f'{exp["abstain_reason_present"]} jawaban'],
    ["Hallucination", f'unsupported claim {hal["unsupported_claim_count"]}, citation '
                      f'mismatch {hal["citation_mismatch_count"]}, archive dipakai '
                      f'untuk pertanyaan current '
                      f'{hal["archive_used_for_current_count"]}, fakta sintetis pada '
                      f'blocker/conflict {hal["synthetic_fact_on_blocker_count"]}, '
                      f'pelanggaran PII {hal["pii_violation_count"]}'],
], [80, 410]))

A(Paragraph("7. Error Analysis", H2))
rows = [[e["evaluation_id"], e["error_category"], e["cause"], e["fix"]]
        for e in evalj["errors"]]
A(tbl(["ID", "Kategori", "Penyebab", "Perbaikan disarankan"], rows,
      [48, 78, 190, 174]))
A(Paragraph(
    "Tidak ada kategori ARCHIVE_LEAKAGE, WRONG_LIFECYCLE, FRESHNESS_FAILURE, "
    "CONTROL_FAILURE, CITATION_MISMATCH, UNSUPPORTED_GENERATION, maupun "
    "OUT_OF_SCOPE_FAILURE yang terjadi. Tidak ada corpus atau gold answer yang diubah "
    "untuk menaikkan skor.", BODY))

A(PageBreak())
A(Paragraph("8. QA Registry Q01-Q18", H2))
rows = [[q["qa_id"], q["description"], q["status"], q["evidence"]]
        for q in evalj["qa_registry"]]
A(tbl(["ID", "Deskripsi", "Status", "Evidence"], rows, [30, 120, 48, 292]))

A(Paragraph("9. Keputusan Gate", H2))
A(Paragraph(
    "Retrieval Gate: CONDITIONAL_PASS. Seluruh kriteria fungsional terpenuhi — 30 "
    "CORE selesai diuji, isolasi filter/lifecycle berfungsi (namespace accuracy 1.00, "
    "isolasi historis 1.00), keputusan kontrol benar 36/36, metrik lengkap, nol "
    "archive leakage, dan tidak ada blocker yang berubah menjadi fakta. Kriteria "
    "reproduksibilitas dengan encoder yang dimandatkan TIDAK terpenuhi, sehingga gate "
    "tidak dapat dinyatakan PASS.", BODY))
A(Paragraph(
    "Baseline RAG Gate: CONDITIONAL_PASS. Jawaban dibangun dari retrieved context, "
    "seluruh citation dapat ditelusuri, abstain/escalate/handoff/ask-context berjalan "
    "sesuai control registry, pemeriksaan halusinasi menghasilkan nol temuan, dan "
    "tidak ada pelanggaran PII. Namun retrieval yang menjadi dasar jawaban bukan "
    "vector search yang dimandatkan.", BODY))
A(Paragraph("Ready for Multi-Agent Implementation: NO. Tahap multi-agent tidak boleh "
            "dimulai sebelum retrieval berbasis encoder E5 dijalankan ulang dan kedua "
            "gate dinaikkan menjadi PASS.", WARN))

A(Paragraph("10. Batas Tahap", H2))
A(Paragraph(
    "Paket ini tidak mencakup implementasi multi-agent, Coordinator Agent final, "
    "antarmuka aplikasi, deployment, maupun fine-tuning. Corpus, embedding, dan vector "
    "database tidak dimodifikasi. Pekerjaan berhenti pada keputusan Ready for "
    "Multi-Agent Implementation.", BODY))
A(Spacer(1, 8))
A(Paragraph("Lampiran: daftar 36 evaluasi dan grade", H2))
rows = [[r["evaluation_id"], r["test_set"], r["expected_response_mode"],
         r["response_mode_applied"], r["grade"], r["error_category"]]
        for r in evalj["rows"]]
A(tbl(["ID", "Set", "Mode diharapkan", "Mode diterapkan", "Grade", "Error"], rows,
      [55, 62, 85, 85, 105, 98]))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(20 * mm, 12 * mm,
                      "Baseline_RAG_Retrieval_Test_RAG_AMIKOM_V1 | Scope FROZEN | "
                      "Retrieval Gate CONDITIONAL_PASS")
    canvas.drawRightString(190 * mm, 12 * mm, f"Halaman {doc.page}")
    canvas.restoreState()


path = os.path.join(OUT, "Laporan_Baseline_RAG_Retrieval_Test_RAG_AMIKOM_V1.pdf")
doc = BaseDocTemplate(path, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                      topMargin=16 * mm, bottomMargin=18 * mm,
                      title="Laporan Baseline RAG dan Retrieval Testing RAG AMIKOM V1",
                      author="Tim UAS PDM")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="n")
doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=footer)])
doc.build(story)
print("pdf written", path)
