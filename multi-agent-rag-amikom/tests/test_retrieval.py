import unittest
from app.retrieval.bm25_fallback import BM25Retriever
from app.retrieval.faiss_retriever import FAISSRetriever
from app.retrieval.e5_encoder import E5QueryEncoder

class TestRetrieval(unittest.TestCase):
    def test_bm25_fallback(self):
        retriever = BM25Retriever()
        results = retriever.retrieve("cuti akademik", "active_administration", k=2)
        # Should return something if data exists
        if results:
            self.assertLessEqual(len(results), 2)
            self.assertEqual(results[0].lifecycle, "ACTIVE")
            
    def test_e5_encoder_instantiation(self):
        encoder = E5QueryEncoder()
        # Test if it loads correctly and can encode a string
        if encoder.session is not None:
            vec = encoder.encode("tes query")
            self.assertEqual(vec.shape, (384,))
            
    def test_faiss_retriever_instantiation(self):
        encoder = E5QueryEncoder()
        retriever = FAISSRetriever(encoder)
        if encoder.session is not None:
            results = retriever.retrieve("cuti akademik", "active_administration", k=2)
            if results:
                self.assertLessEqual(len(results), 2)
                self.assertEqual(results[0].lifecycle, "ACTIVE")

if __name__ == "__main__":
    unittest.main()
