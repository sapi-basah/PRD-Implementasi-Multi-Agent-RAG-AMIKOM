# Baseline RAG dan Retrieval Testing — RAG AMIKOM V1

## Status

- Scope Status: **FROZEN**
- Vector Database Gate (tahap sebelumnya): **PASS** (diverifikasi ulang)
- Retrieval Testing: **PARTIALLY_COMPLETE**
- Baseline Top-k: **5** (sementara)
- Baseline RAG: **COMPLETE**
- Retrieval Gate: **CONDITIONAL_PASS**
- Baseline RAG Gate: **CONDITIONAL_PASS**
- Ready for Multi-Agent Implementation: **NO**
- Multi-Agent Executed: **NO**

## Peringatan utama sebelum memakai angka apa pun

Query encoder yang dimandatkan — `Xenova/multilingual-e5-small`
revisi `761b726dd34fb83930e26aab4e9ac3899aa1fa78` — **tidak dapat dijalankan**
pada lingkungan eksekusi: `huggingface.co` diblokir proxy (CONNECT tunnel 403)
dan artefak model tidak dibundel pada paket input mana pun.

Konsekuensinya:

- tidak ada query vector 384-dimensi yang dihasilkan;
- **FAISS search tidak dijalankan** untuk 36 query evaluasi;
- retrieval memakai pengganti deterministik `FALLBACK_LEXICAL_BM25_V1`
  (BM25 Okapi, k1=1.5, b=0.75, field `title` + `chunk_text`);
- **Hit@k, Recall@k, Precision@k, dan MRR pada paket ini tidak mewakili
  performa vector search E5**;
- `baseline_top_k = 5` hanya valid untuk backend leksikal dan wajib
  ditinjau ulang setelah encoder tersedia.

Skor pada kolom `similarity_scores` adalah skor BM25, **bukan cosine similarity**.

## Yang tetap teruji secara sah

Lapisan yang tidak bergantung pada encoder tetap diuji penuh dan hasilnya valid:

| Aspek | Hasil |
|---|---|
| Validasi input (6 artefak, SHA-256) | PASS, identik dengan `final_package_validation.json` |
| FAISS reload + smoke test | ntotal 306, dim 384, self-match skor 1.0 |
| SQLite | 306 record, vector_index 0–305, dibuka read-only |
| Filter sebelum ranking | PASS (kandidat dari SQLite dulu, tanpa global top-k) |
| Namespace/filter accuracy | 1.00 (36 query) |
| Isolasi historis | 1.00 (3 query ARCHIVE) |
| Archive leakage pada query current | 0 |
| Control decision accuracy | 1.00 (36/36) |
| Freshness ACTIVE_DYNAMIC | 10 record kedaluwarsa → LIVE_CHECK_OR_ABSTAIN |
| Unsupported claim / citation mismatch / pelanggaran PII | 0 / 0 / 0 |

## Metrik retrieval (backend leksikal, subset ber-skor 20 query)

| k | Hit@k | Recall@k | Precision@k | MRR@k | Chunk tak relevan | Token context |
|---|---|---|---|---|---|---|
| 1 | 0.65 | 0.32 | 0.65 | 0.65 | 0.35 | 69 |
| 3 | 0.80 | 0.65 | 0.55 | 0.73 | 1.35 | 209 |
| **5** | **0.80** | **0.73** | **0.40** | **0.73** | **3.00** | **345** |
| 10 | 0.95 | 0.91 | 0.31 | 0.74 | 6.40 | 616 |

Subset ber-skor = 20 query yang menuntut retrieval faktual
(`expected_response_mode` ANSWER atau ASK_CONTEXT) **dan** memiliki minimal satu
gold chunk di dalam database. 16 query sisanya adalah kasus kontrol
(ABSTAIN/ESCALATE/REFUSE) yang gold chunk-nya berupa record
CONTROL/CONFLICT/BLOCKED yang memang tidak diindeks (FV11); kasus itu dinilai
lewat control decision accuracy, bukan Hit@k.

## Hasil baseline RAG (36 evaluasi)

15 PASS · 6 PARTIAL · 2 ABSTAIN_CORRECT · 4 HANDOFF_CORRECT ·
9 OUT_OF_SCOPE_CORRECT · **0 FAIL**

Response mode benar 36/36. Enam PARTIAL seluruhnya disebabkan retrieval leksikal
yang gagal mengangkat gold chunk (EV-A01, EV-A05, EV-D06, EV-C01, EV-C05, EV-C06),
bukan karena generator berhalusinasi — pada semua kasus tersebut generator justru
menyatakan informasi tidak ditemukan.

## Isi paket

```
00_manifest/   Manifest_Retrieval_Test_RAG_AMIKOM_V1.xlsx (12 sheet), hash registry
01_config/     Retrieval_Config_RAG_AMIKOM_V1.json
02_results/    Retrieval_Results_CORE.jsonl, Retrieval_Results_SUPPLEMENTARY.jsonl,
               Baseline_RAG_Answers.jsonl, context_packs.json
03_evaluation/ baseline_rag_evaluation.json, retrieval_metrics.json,
               generation_autochecks.json, Error_Analysis_RAG_AMIKOM_V1.xlsx
04_qa/         database_validation.json, qa_registry.csv, gate.json
05_checkpoint/ checkpoint per 10 evaluasi
06_logs/       kode pipeline yang dijalankan (ragx/, runner, metrik, evaluator)
Laporan_Baseline_RAG_Retrieval_Test_RAG_AMIKOM_V1.pdf
README_Baseline_RAG_Retrieval_Test.md
Retrieval_Recovery_Prompt.md
```

## Cara reproduksi

```bash
python3 build/db_validation.py      # validasi hash + FAISS/SQLite
python3 build/run_retrieval.py      # 36 query x k=1,3,5,10
python3 build/metrics.py            # metrik retrieval + top-k comparison
python3 build/assemble_context.py   # context k=5 + control directive
# generator LLM tunggal -> Baseline_RAG_Answers.jsonl
python3 build/check_generation.py   # citation + hallucination + PII
python3 build/evaluate.py           # grade, error analysis, QA, gate
python3 build/build_manifest.py build/build_report.py build/build_package.py
```

Pipeline retrieval bersifat deterministik: menjalankan ulang menghasilkan
peringkat dan skor yang identik. Tahap generasi memakai LLM sehingga teks jawaban
dapat sedikit berbeda; keputusan mode dan sitasi terikat pada control directive
dan context yang sama.

## Batas tahap

Paket ini **tidak** mencakup implementasi multi-agent, Coordinator Agent final,
antarmuka aplikasi, deployment, atau fine-tuning. Corpus, embedding, dan vector
database tidak dimodifikasi.
