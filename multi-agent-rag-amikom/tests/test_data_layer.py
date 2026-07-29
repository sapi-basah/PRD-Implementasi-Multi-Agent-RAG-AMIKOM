import unittest
from app.data import metadata_store, vector_store, chunk_corpus_store

class TestDataLayer(unittest.TestCase):
    def test_metadata_store_dimension(self):
        dim = metadata_store.get_dimension()
        self.assertEqual(dim, 384, "Embedding dimension should be 384")

    def test_metadata_store_record_count(self):
        count = metadata_store.get_record_count()
        self.assertEqual(count, 306, "Expected 306 embedding records")

    def test_metadata_store_namespaces(self):
        records = metadata_store.fetch_all_records()
        self.assertGreater(len(records), 0)
        
        # Test historical_only isolation (archive_schedule)
        historical_records = metadata_store.filter_records(historical_only=1)
        for r in historical_records:
            self.assertEqual(r["retrieval_namespace"], "archive_schedule")
            
        # Test active_academic
        academic_records = metadata_store.filter_records(retrieval_namespace="active_academic")
        self.assertGreater(len(academic_records), 0)
        
    def test_vector_store_available(self):
        self.assertTrue(vector_store.is_available(), "Vector store should be available with FAISS")
        
    def test_chunk_corpus_store(self):
        chunks = chunk_corpus_store.get_all_chunks()
        self.assertGreaterEqual(len(chunks), 306, "Should have at least 306 chunks")
        
        # Lookup a specific chunk if it exists
        if chunks:
            first_chunk = chunks[0]
            chunk_id = first_chunk["chunk_id"]
            retrieved = chunk_corpus_store.get_chunk(chunk_id)
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved["chunk_id"], chunk_id)

if __name__ == "__main__":
    unittest.main()
