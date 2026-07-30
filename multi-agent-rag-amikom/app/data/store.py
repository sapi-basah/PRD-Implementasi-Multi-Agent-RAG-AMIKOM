"""Data store: MetadataStore (SQLite) dan VectorStore (FAISS)."""

import os
import sqlite3
from typing import Any, Dict, List, Optional

from app.config.settings import settings
from app.observability import logger

try:
    import numpy as np
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS module not found. Vector retrieval will fall back to BM25.")


class MetadataStore:
    """Akses metadata SQLite untuk filter sebelum FAISS ranking."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or settings.SQLITE_METADATA_PATH

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def fetch_all_records(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.db_path):
            logger.warning(f"Metadata DB file missing: {self.db_path}")
            return []
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vector_records")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_record_count(self) -> int:
        if not os.path.exists(self.db_path):
            return 0
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vector_records")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_dimension(self) -> int:
        if not os.path.exists(self.db_path):
            return 0
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT vector_dimension FROM vector_records LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0

    def filter_records(
        self,
        retrieval_namespace: Optional[str] = None,
        lifecycle_status: Optional[str] = None,
        historical_only: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Filter metadata records sebelum FAISS similarity ranking (metadata-first)."""
        if not os.path.exists(self.db_path):
            return []
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM vector_records WHERE 1=1"
        params: list = []

        if retrieval_namespace:
            query += " AND retrieval_namespace = ?"
            params.append(retrieval_namespace)
        if lifecycle_status:
            query += " AND lifecycle_status = ?"
            params.append(lifecycle_status)
        if historical_only is not None:
            query += " AND historical_only = ?"
            params.append(historical_only)

        cursor.execute(query, params)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_record_by_chunk_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.db_path):
            return None
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vector_records WHERE chunk_id = ?", (chunk_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_records_by_source_id(self, source_id: str) -> List[Dict[str, Any]]:
        if not os.path.exists(self.db_path):
            return []
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vector_records WHERE source_id = ?", (source_id,))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows


class VectorStore:
    """FAISS vector index untuk similarity search."""

    def __init__(self, index_path: str | None = None):
        self.index_path = index_path or settings.FAISS_INDEX_PATH
        self.index = None
        self._load_index()

    def _load_index(self):
        if FAISS_AVAILABLE and os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                logger.info(
                    f"FAISS index loaded: {self.index_path} ({self.index.ntotal} vectors)"
                )
            except Exception as e:
                logger.error(f"Failed to read FAISS index: {e}")
                self.index = None
        else:
            logger.info("FAISS index unavailable. System operating in degraded/BM25 mode.")

    def is_available(self) -> bool:
        return self.index is not None and self.index.ntotal > 0

    def search(
        self,
        query_vector,
        candidate_indices: List[int],
        k: int,
    ) -> List[Dict[str, Any]]:
        """FAISS search yang hanya dilakukan pada candidate indices (metadata-first)."""
        import numpy as np

        if not self.is_available():
            return []

        if not candidate_indices:
            return []

        # Ensure query is 2D float32
        q = np.array([query_vector], dtype=np.float32)
        actual_k = min(k, len(candidate_indices))

        # Create IDSelector to filter candidates
        candidate_ids_array = np.array(candidate_indices, dtype=np.int64)

        try:
            id_selector = faiss.IDSelectorBatch(candidate_ids_array)
            search_params = faiss.SearchParameters(sel=id_selector)
            distances, indices = self.index.search(q, actual_k, params=search_params)

            results = []
            for j, idx in enumerate(indices[0]):
                if idx != -1:
                    results.append(
                        {"vector_index": int(idx), "score": float(distances[0][j])}
                    )
            return results
        except Exception:
            # Fallback: brute force filter if SearchParameters not supported
            try:
                distances, indices = self.index.search(q, self.index.ntotal)
                results = []
                candidate_set = set(candidate_indices)
                for j, idx in enumerate(indices[0]):
                    if idx in candidate_set:
                        results.append(
                            {"vector_index": int(idx), "score": float(distances[0][j])}
                        )
                        if len(results) >= k:
                            break
                return results
            except Exception as e:
                logger.error(f"FAISS search failed: {e}")
                return []


metadata_store = MetadataStore()
vector_store = VectorStore()
