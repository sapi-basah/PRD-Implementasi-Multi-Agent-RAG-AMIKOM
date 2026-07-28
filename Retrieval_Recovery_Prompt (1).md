# Retrieval Recovery Prompt — RAG AMIKOM V1

Gunakan prompt ini untuk **mengulang tahap Retrieval Testing dengan encoder yang
dimandatkan** setelah artefak model tersedia. Jangan memulai tahap multi-agent
sebelum langkah ini selesai dan kedua gate naik menjadi PASS.

## 1. Kondisi saat ini

- Scope Status: FROZEN — corpus, embedding, dan vector database **tidak boleh diubah**.
- Vector Database Gate: PASS (306 vector, dim 384, hash terverifikasi).
- Retrieval Testing: PARTIALLY_COMPLETE.
- Retrieval Gate: CONDITIONAL_PASS. Baseline RAG Gate: CONDITIONAL_PASS.
- Ready for Multi-Agent: NO. Multi-Agent Executed: NO.
- Penyebab tunggal status kondisional:
  `QUERY_ENCODER_UNAVAILABLE` — `huggingface.co` diblokir proxy sandbox (403),
  artefak model tidak dibundel pada paket input.

## 2. Prasyarat yang harus dipenuhi lebih dulu

Sediakan empat artefak model repo `Xenova/multilingual-e5-small`
revisi `761b726dd34fb83930e26aab4e9ac3899aa1fa78` secara offline dan verifikasi
SHA-256 terhadap `Embedding_Config_RAG_AMIKOM_V1.json`:

| File | Ukuran (byte) | SHA-256 |
|---|---|---|
| `config.json` | 658 | `cb99455288675345e1a4f411438d5d0adbba5fbd3a67ea4fb03c015433b996c1` |
| `tokenizer.json` | 17.082.730 | `0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39` |
| `tokenizer_config.json` | 443 | `a1d6bc8734a6f635dc158508bef000f8e2e5a759c7d92f984b2c86e5ff53425b` |
| `onnx/model_int8.onnx` | 118.054.593 | `4d24e2bc01a447951524466ef533e52944bf48509e6552810bcee1a2711cb02c` |

Jika salah satu hash tidak cocok, hentikan dan laporkan; jangan memakai revisi lain.

## 3. Prompt eksekusi

> LANJUTKAN PROJECT UAS PDM: ULANG TAHAP RETRIEVAL TESTING DENGAN ENCODER RESMI.
>
> Input wajib: `Vector_Database_RAG_AMIKOM_V1.zip`,
> `Vector_Database_Config_RAG_AMIKOM_V1.json`,
> `Manifest_Vector_Database_RAG_AMIKOM_V1.xlsx`,
> `Laporan_Vector_Database_Indexing_RAG_AMIKOM_V1.pdf`,
> `README_Vector_Database_RAG_AMIKOM_V1.md`, `final_package_validation.json`,
> `Embedding_Config_RAG_AMIKOM_V1.json`, `Chunk_Corpus_RAG_AMIKOM_V1.zip`,
> `Baseline_RAG_Retrieval_Test_RAG_AMIKOM_V1.zip` (paket ini), serta empat artefak
> model pada tabel di atas.
>
> Langkah:
> 1. Verifikasi ulang SHA-256 seluruh input; pastikan FAISS 306 vector, SQLite 306
>    record, dimensi 384; buka database read-only.
> 2. Muat model E5 dari artefak lokal, revisi 761b726dd34fb83930e26aab4e9ac3899aa1fa78,
>    tokenizer resmi, mean pooling, normalisasi L2, float32, dimensi 384.
> 3. Encode 36 pertanyaan dengan prefix `query: ` (jangan `passage: `). Validasi tiap
>    vector: dimensi 384, tanpa NaN/Infinity/zero, norm mendekati 1. Simpan hasil
>    validasi sebagai bukti QA Q02 dan Q03.
> 4. Pertahankan lapisan kontrol dan filter apa adanya dari `build/ragx/control.py`
>    dan `build/ragx/store.py` paket ini — keduanya sudah lulus (control accuracy
>    1.00, namespace accuracy 1.00, archive leakage 0). Ganti HANYA modul scoring:
>    `FALLBACK_LEXICAL_BM25_V1` menjadi FAISS inner-product pada himpunan kandidat
>    hasil SQLite (`IDSelectorArray` atau rekonstruksi sub-index kandidat).
>    Filter tetap dijalankan SEBELUM ranking; dilarang global top-k lalu buang.
> 5. Jalankan ulang k = 1, 3, 5, 10 untuk 30 CORE dan 6 SUPPLEMENTARY. Hitung ulang
>    Hit@k, Recall@k, Precision@k, MRR, source accuracy, namespace accuracy, control
>    accuracy, archive isolation, dan latency (kini termasuk latency encoder).
> 6. Tetapkan ulang `baseline_top_k` dari hasil 30 CORE, bukan dari nilai 5 pada
>    paket ini. Bandingkan eksplisit terhadap tabel BM25 di
>    `02_TopK_Comparison` sebagai baseline pembanding.
> 7. Jalankan ulang baseline RAG satu generator dengan kontrak prompt yang sama,
>    lalu evaluasi accuracy, effectiveness, efficiency, explainability, hallucination.
> 8. Tinjau ulang enam error berikut dan nyatakan apakah teratasi oleh retrieval
>    semantik: EV-A01 (WRONG_SOURCE), EV-A05 (RETRIEVAL_MISS), EV-D06
>    (RETRIEVAL_MISS), EV-C01 (RETRIEVAL_MISS), EV-C05 (ROUTING_ERROR), EV-C06
>    (FILTER_ERROR).
> 9. Perbarui QA: Q02 dan Q03 wajib menjadi PASS; Q17 menjadi PASS hanya jika hasil
>    dapat direproduksi byte-identik dengan model yang sama.
> 10. Tetapkan Retrieval Gate dan Baseline RAG Gate secara jujur. Jangan memaksakan
>     PASS. Ready for Multi-Agent = YES hanya bila kedua gate PASS.
>
> Larangan: mengubah corpus, embedding, vector database, atau gold answer; memakai
> gold chunk untuk mengatur hasil retrieval; memulai implementasi multi-agent,
> Coordinator Agent final, antarmuka, deployment, atau fine-tuning.

## 4. Perbaikan yang disarankan untuk dijalankan bersamaan

1. **Retrieval per namespace lalu merge** (round-robin atau kuota per sub-intent)
   agar namespace besar tidak menenggelamkan namespace kecil — penyebab EV-C05
   (271 kandidat akademik vs 25 administrasi) dan EV-C06 (mode MIXED).
2. **Diversifikasi per source** (maksimal n chunk per `source_id` sebelum merge)
   agar gold prosedural multi-chunk tidak kalah oleh satu dokumen dominan (EV-D06).
3. **Tie-break `source_priority`** ketika skor berdekatan, agar sumber otoritatif
   menang atas sumber sekunder yang kebetulan cocok secara leksikal (EV-A01).
4. **Held-out control cases**: tambahkan 10–15 kasus baru di luar registry 36 kasus
   untuk menguji apakah control accuracy 1.00 bertahan, karena aturan kontrol saat
   ini dikalibrasi pada registry yang sama dengan set evaluasi.

## 5. Jika resource habis di tengah jalan

Selesaikan query yang sedang berjalan, simpan hasil ke
`02_results/`, tetapkan status `PARTIALLY_COMPLETE`, perbarui change log,
dan **jangan** memulai implementasi multi-agent.
