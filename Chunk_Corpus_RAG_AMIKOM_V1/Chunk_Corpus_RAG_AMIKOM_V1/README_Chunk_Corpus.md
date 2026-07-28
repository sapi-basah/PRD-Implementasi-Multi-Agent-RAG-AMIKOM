# Chunk Corpus RAG AMIKOM V1

## Status paket

- Scope Status: **FROZEN**
- Clean Corpus Gate: **PASS**
- Chunking Status: **COMPLETE**
- Chunk Corpus Gate: **PASS**
- Ready for Embedding: **YES**
- Embedding Executed: **NO**
- Ready for Vector Database: **NO**
- Ready for Retrieval Testing: **NO**
- Ready for Multi-Agent: **NO**

Tahap ini berhenti pada Chunk Corpus Gate dan keputusan Ready for Embedding.

## Struktur dan format

Setiap berkas `*.jsonl` memakai satu objek JSON UTF-8 per baris. Berkas
`Chunk_Corpus_RAG_AMIKOM_V1.jsonl` hanya berisi chunk dengan
`embedding_candidate=true`. Conflict, blocker, dan control tetap tersedia
di JSONL terpisah dan tidak masuk gabungan embedding.

Folder `01_active` sampai `06_control` adalah indeks namespace. Rekaman
kanonik berada pada delapan JSONL lifecycle/domain di akar paket agar satu
chunk tidak diduplikasi secara fisik maupun semantik.

## Konvensi chunk ID

`CH-{NAMESPACE}-{SOURCE_ID}-{DOCUMENT_ID}-{TYPE}-{INDEX}`

Index dimulai dari `0001` per kombinasi `document_id` dan `chunk_type`.
Versi chunk berbasis 12 karakter awal SHA-256 isi. Hash penuh dihitung atas
`chunk_text` UTF-8.

## Tokenizer referensi

`unicode_codepoint_v1; Unicode 15.0.0; Python stdlib unicodedata; NFC normalization`

Satu token adalah satu Unicode code point setelah normalisasi NFC. Ini
bukan jumlah kata dan bukan tokenizer model embedding. Tokenizer alternatif
ini dipakai konsisten karena `cl100k_base`/tokenizer model tidak tersedia.
Model embedding final harus melakukan pengukuran ulang tanpa mengubah
chunk_id kecuali isi chunk benar-benar berubah.

## Strategi chunking

- Naratif: section-aware, tidak melintasi heading; unit atomik digabung
  sampai target, tanpa overlap karena tidak diperlukan.
- A10: 67 `COURSE_ROW`.
- A11: 67 `COURSE_NODE`; relasi ambigu tidak ditulis sebagai fakta.
- A12: 52 `EQUIVALENCY_ROW`.
- A03: 10 `CURRENT_EVENT`, TTL satu hari dan live check wajib.
- A04/A05/D01: 25 `ARCHIVE_EVENT`, historical-only.
- B01–B07: procedure-aware; purpose/requirements, steps/channel, dan
  privacy/handoff dipisahkan bila perlu.
- CF002: dua klaim terpisah, tidak memilih pemenang.
- G02: blocker control tanpa tanggal sintetis.
- INT01–INT07, G01, CF001, dan MR-A11-RELATIONS: control-only.

## Metadata penting

Field mencakup identitas chunk, traceability clean/raw, locator, lifecycle,
agent/retrieval namespace, freshness, validity, TTL, autentikasi, handoff,
PII, embedding eligibility, serta metadata khusus course, equivalency,
event, procedure, conflict, blocker, dan control.

`NOT_AVAILABLE` berarti nilai tidak tersedia. `NOT_APPLICABLE` berarti
field tidak relevan untuk chunk tersebut.

## Lifecycle dan batas penggunaan

- ACTIVE dan ACTIVE_DYNAMIC dapat menjadi embedding candidate.
- ACTIVE_DYNAMIC selalu memerlukan freshness check.
- ARCHIVE menjadi embedding candidate hanya untuk namespace arsip dan
  `active_retrieval_allowed=false`.
- CONFLICT, BLOCKED, dan CONTROL tidak menjadi embedding candidate.
- Tidak ada chunk OUT_OF_SCOPE/REJECTED.
- Data personal, credential, nilai, transkrip, keuangan, dan dokumen
  identitas tidak boleh dikirim ke chatbot.

## Blocker dan konflik yang tetap

- G01: `PARTIALLY_RESOLVED_ACCEPTED_BLOCKER`; kalender dinamis, TTL 1 hari.
- G02: `OPEN_ACCEPTED_BLOCKER`; agenda Ganjil 2026/2027 belum dipublikasikan.
- G04: `PARTIALLY_RESOLVED`; precedence kode ada, CF002 tetap terbuka.
- CF002: `OPEN_ACCEPTED_BLOCKER`; klaim ambang IPK tepat 2,00 berkonflik.
- MR-A11-RELATIONS: relasi panah ambigu tidak boleh ditebak.

## Evaluasi dan QA

- 30/30 CORE memiliki coverage atau accepted blocker yang sah.
- 6/6 SUPPLEMENTARY berstatus OUT_OF_SCOPE.
- 32 chunk (10.0%) ditinjau lintas source/type/lifecycle.
- Q01–Q25: 25 PASS, 0 FAIL.

## Verifikasi hash

Hitung SHA-256 `chunk_text` UTF-8 dan cocokkan dengan `chunk_hash`, atau
gunakan `00_manifest/chunk_hash_registry.csv`. Hash berkas paket tercatat
di inventory final setelah ZIP dibuat.

## Batas tahap

Paket ini belum membuat embedding, vector database, retriever, pengujian
semantic retrieval, Coordinator Agent, atau implementasi multi-agent.
