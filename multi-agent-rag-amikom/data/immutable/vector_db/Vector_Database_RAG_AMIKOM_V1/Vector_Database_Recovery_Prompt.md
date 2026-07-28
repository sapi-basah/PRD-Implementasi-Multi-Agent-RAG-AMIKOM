# Vector Database Recovery Prompt

Continue `Vector_Database_RAG_AMIKOM_V1` only after validating the six immutable inputs
and config hash `9c742bb4917a97de92e3341e772ac9a06d6984a6c33e9f0456adc5b8b669245c`.

1. Load the existing SQLite metadata store and FAISS index.
2. Validate that SQLite row count equals FAISS `ntotal`.
3. Validate every COMPLETE checkpoint and batch vector hash.
4. Skip COMPLETE batches; continue only the first missing or invalid batch.
5. Use the same FAISS 1.14.3, `IndexIDMap2(IndexFlatIP)`, dimension 384, cosine-via-IP
   configuration, and vector_index IDs.
6. Persist, close, reopen, and repeat Q01-Q18 plus filter smoke tests.
7. If counts or hashes diverge, stop with PARTIALLY_COMPLETE; do not run retrieval testing.

Do not recompute embeddings, change source metadata, determine top-k, run retrieval
evaluation, create baseline RAG, or implement multi-agent behavior in recovery.
