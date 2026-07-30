# Matriks Tanggung Jawab Agent — Multi-Agent RAG AMIKOM V1.1

## Matriks Peran dan Namespace

| Agent | In-Scope Domain | Allowed Namespace | Forbidden Action |
|---|---|---|---|
| **Coordinator Agent** | Query classification, temporal mode, query decomposition, agent routing, result merging | None (Tidak memiliki knowledge namespace) | Tidak boleh menulis atau menyintesis fakta baru |
| **Academic Agent** | Kurikulum 2025, mata kuliah, SKS, konsentrasi, penyetaraan, syarat kelulusan | `active_academic` | Tidak boleh mengambil data jadwal/arsip; tidak boleh memilih sendiri klaim CF002 |
| **Schedule Agent** | Kalender akademik, jadwal KRS, jadwal ujian, perkuliahan | `active_schedule`, `active_dynamic_schedule`, `archive_schedule` | Current mode tidak boleh mengambil `archive_schedule`; Historical mode hanya mengambil `archive_schedule`; tidak boleh menebak tanggal belum rilis |
| **Administration Agent** | KRS manual, cuti akademik, SKAK, legalisir ijazah/transkrip, KTM, PDDIKTI | `active_administration` | Tidak memproses nilai, status transaksi, dokumen personal, atau data identitas |
| **Pre-Control & Verifier** | Guardrails, PII redaction, scope compliance, conflict/blocker handling | Reads control/conflict/blocked registries | Tidak boleh mengabaikan pelanggaran kritis |
