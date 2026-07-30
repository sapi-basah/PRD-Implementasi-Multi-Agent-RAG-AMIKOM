# Keterbatasan & Rencana Pengembangan Masa Depan — Multi-Agent RAG AMIKOM V1.1

## Keterbatasan Saat Ini (Limitations)
1. **Final Gold Dataset Pending**: File `Final_Multi_Agent_Foundation_Dataset_RAG_AMIKOM_V1.zip` belum tersedia di repository sehingga status 36 human review belum dapat diverifikasi dalam `data/final_gold/`.
2. **Offline LLM Generation**: Sistem saat ini menggunakan `Evidence Selector V2` sebagai fallback deterministik ketika LLM provider tidak dikonfigurasi.
3. **Data Scope**: Terbatas pada Kurikulum/Angkatan 2025 S1 Informatika AMIKOM.

## Rencana Pengembangan Masa Depan (Future Work)
1. Integrasi model LLM lokal (misal Llama-3-8B-Instruct atau Qwen2.5-7B) via Ollama/vLLM.
2. Penambahan modul fine-tuning retriever untuk adaptasi domain yang lebih spesifik.
3. Dukungan multi-turn conversation memory dengan session tracking.
