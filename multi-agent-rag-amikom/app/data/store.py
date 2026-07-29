import os
import sqlite3
import json
from typing import List, Dict, Any, Optional
from app.config import settings
from app.observability import logger

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS module not found. Vector retrieval will fall back to BM25.")

class MetadataStore:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.METADATA_DB_PATH

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def fetch_all_records(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.db_path):
            logger.warning(f"Metadata DB file missing: {self.db_path}")
            return []
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vector_records")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_record_count(self) -> int:
        if not os.path.exists(self.db_path):
            return 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vector_records")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_dimension(self) -> int:
        if not os.path.exists(self.db_path):
            return 0
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT vector_dimension FROM vector_records LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0

    def filter_records(
        self,
        retrieval_namespace: Optional[str] = None,
        lifecycle_status: Optional[str] = None,
        historical_only: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        if not os.path.exists(self.db_path):
            return []
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM vector_records WHERE 1=1"
        params = []

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
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_record_by_chunk_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vector_records WHERE chunk_id = ?", (chunk_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

class VectorStore:
    def __init__(self, index_path: str = None):
        self.index_path = index_path or settings.FAISS_INDEX_PATH
        self.index = None
        self.load_index()

    def load_index(self):
        if FAISS_AVAILABLE and os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                logger.info(f"FAISS index loaded successfully from {self.index_path} with {self.index.ntotal} vectors.")
            except Exception as e:
                logger.error(f"Failed to read FAISS index: {e}")
                self.index = None
        else:
            logger.info("FAISS index unavailable. System operating in degraded/BM25 mode.")

    def is_available(self) -> bool:
        return self.index is not None and self.index.ntotal > 0

    def search(self, query_vector, candidate_indices: List[int], k: int) -> List[Dict[str, Any]]:
        import numpy as np
        if not self.is_available():
            return []
            
        if not candidate_indices:
            return []
            
        # Create IDSelector to filter candidates
        # Convert to numpy array of int64
        candidate_ids_array = np.array(candidate_indices, dtype=np.int64)
        id_selector = faiss.IDSelectorBatch(candidate_ids_array)
        
        # Ensure query is 2D float32
        q = np.array([query_vector], dtype=np.float32)
        
        # Search parameters
        search_params = faiss.SearchParametersIVF(sel=id_selector) if hasattr(faiss, 'SearchParametersIVF') else faiss.SearchParameters(sel=id_selector)
        
        # Perform search
        try:
            # For Flat index, faiss python api might not accept SearchParameters directly in all versions. 
            # If SearchParameters causes issues, we'll try IDSelector directly if supported, or fallback.
            # In FAISS, IDSelector is passed via SearchParameters in newer versions.
            distances, indices = self.index.search(q, min(k, len(candidate_indices)), params=search_params)
            
            results = []
            for j, idx in enumerate(indices[0]):
                if idx != -1:
                    results.append({
                        "vector_index": int(idx),
                        "score": float(distances[0][j])
                    })
            return results
        except Exception as e:
            logger.error(f"FAISS search failed: {e}")
            return []

metadata_store = MetadataStore()
vector_store = VectorStore()
