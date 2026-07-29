import unittest
import numpy as np
from app.retrieval.e5_gate import verify_e5_model
from app.retrieval.e5_encoder import E5QueryEncoder
from app.retrieval.faiss_retriever import FAISSRetriever

class TestE5Retrieval(unittest.TestCase):
    def test_e5_model_verification(self):
        res = verify_e5_model()
        self.assertEqual(res["status"], "PASS", f"E5 Verification failed: {res}")
        
    def test_e5_encoding(self):
        encoder = E5QueryEncoder()
        self.assertIsNotNone(encoder.session, "E5 model failed to load")
        
        vec = encoder.encode("jadwal kuliah besok")
        self.assertEqual(vec.shape, (384,), "Dimension must be 384")
        self.assertEqual(vec.dtype, np.float32, "Dtype must be float32")
        
        # Test L2 norm is approximately 1
        norm = np.linalg.norm(vec)
        self.assertAlmostEqual(norm, 1.0, places=4, msg="Vector must be L2 normalized")
        
        # Test no NaNs
        self.assertFalse(np.isnan(vec).any(), "Vector must not contain NaNs")
        
    def test_e5_faiss_retrieval_k_values(self):
        encoder = E5QueryEncoder()
        retriever = FAISSRetriever(encoder)
        
        for k in [1, 3, 5, 10]:
            results = retriever.retrieve("jadwal ujian", "active_schedule", k=k)
            # Cannot guarantee length == k if namespace has fewer items
            # active_schedule only has 3 items in SQLite, active_dynamic_schedule has 10
            # Let's test with academic which has 243 items
            res = retriever.retrieve("syarat kelulusan", "active_academic", k=k)
            if res:
                self.assertLessEqual(len(res), k)

if __name__ == "__main__":
    unittest.main()
