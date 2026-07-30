# Dokumentasi Implementasi Retrieval — Multi-Agent RAG AMIKOM V1.1

## Komponen Retrieval

1. **E5 Query Encoder**:
   - Model: `Xenova/multilingual-e5-small` (ONNX format)
   - Formatting: Prefix `"query: "` ditambahkan otomatis ke pertanyaan pengguna.
   - Output: Vektor Float32 berdimensi 384 dengan L2 normalization. Validasi ketat memastikan tidak ada vektor NaN, Inf, atau zero-vector.

2. **SQLite Metadata Candidate Filtering (Metadata-First)**:
   - Sebelum melakukan similarity search di FAISS, metadata SQLite difilter terlebih dahulu berdasarkan `retrieval_namespace`, `lifecycle_status`, dan `historical_only`.
   - Hanya kandidat `vector_index` yang lolos filter yang dilewatkan ke FAISS search.

3. **FAISS Inner Product Ranking**:
   - FAISS melakukan pencarian similarity pada subset kandidat yang telah difilter.
   - Hasil diurutkan berdasarkan skor kemiripan tertinggi.

4. **BM25 Fallback**:
   - Digunakan hanya jika model E5 atau ONNX runtime tidak tersedia.
   - Setiap respon dari BM25 fallback ditandai dengan `retrieval_backend=BM25_FALLBACK` dan readiness `DEGRADED`.
