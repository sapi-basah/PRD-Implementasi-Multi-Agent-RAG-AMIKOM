# Decision Log — Multi-Agent RAG AMIKOM V1.1

## Catatan Keputusan

1. **Keputusan Status Dataset Baseline vs Gold (2026-07-30)**
   - **Keputusan:** Menggunakan `Baseline_RAG_Retrieval_Test_RAG_AMIKOM_V1` sebagai provisional test fixture.
   - **Rationale:** ZIP `Final_Multi_Agent_Foundation_Dataset_RAG_AMIKOM_V1.zip` tidak ada di repo, sehingga 36 HUMAN_PASS dicatat pada `MISSING_FINAL_DATASET_REPORT.md` dan `final_ready` dijaga tetap `false`.

2. **Keputusan LLM Fallback (2026-07-30)**
   - **Keputusan:** Menggunakan `Evidence Selector V2` sebagai generator fallback deterministik ketika LLM provider tidak terkonfigurasi.
   - **Rationale:** Memastikan sistem tetap 100% dapat dijalankan dan diuji tanpa memerlukan API key eksternal.

3. **Keputusan Metadata-First FAISS Candidate Search (2026-07-30)**
   - **Keputusan:** Mengueri kandidat index dari SQLite berdasarkan `retrieval_namespace` dan `historical_only` sebelum memanggil FAISS.
   - **Rationale:** Mencegah archive leakage dan persilangan antar domain akademik, jadwal, dan administrasi.
