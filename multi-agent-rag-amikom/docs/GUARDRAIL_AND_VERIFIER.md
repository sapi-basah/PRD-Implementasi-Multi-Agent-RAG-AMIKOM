# Dokumentasi Verifier & Guardrail — Multi-Agent RAG AMIKOM V1.1

## Kategori Pengujian Guardrail (13 Checks)

1. **PII Detection**: Menolak input dan mengaburkan (redact) output yang memuat NIM, email, nomor HP, KTP, atau kredensial.
2. **Out-of-Scope Control**: Menolak pertanyaan di luar domain S1 Informatika (SPP, beasiswa, karir/magang, prodi lain).
3. **Lifecycle Check**: Memastikan status chunk sesuai dengan konteks query.
4. **Current / Historical Leakage**: Memastikan mode CURRENT tidak menggunakan `archive_schedule` (leakage = 0), dan mode HISTORICAL hanya menggunakan `archive_schedule`.
5. **Freshness & TTL**: Memberikan warning pada chunk `active_dynamic_schedule` yang dinamis.
6. **Conflict CF002**: Menangani ambiguitas aturan batas IPK 2.00 dengan mengeskalasi (ESCALATE) ke DPA/BAAK.
7. **Blocker G02**: Menolak (ABSTAIN) informasi jadwal atau pengumuman yang belum dipublikasikan secara resmi.
8. **Citation Support**: Memastikan setiap klaim didukung oleh citation valid (`source_id`, `chunk_id`, `locator`).
9. **Unsupported Factual Claim**: Mengidentifikasi klaim tanpa bukti retrieval.
10. **Empty Evidence Check**: Menangani kasus ketika tidak ada chunk yang relevan.
11. **Source / Chunk / Locator Mismatch**: Menolak citation yang tidak terdapat dalam evidence yang dipakai.
12. **Synthetic Date / Fact Detection**: Mencegah LLM mengarang tanggal di masa depan.
13. **Credential & Personal Data Request**: Menolak/handoff permintaan transaksi, nilai, dan dokumen identitas.
