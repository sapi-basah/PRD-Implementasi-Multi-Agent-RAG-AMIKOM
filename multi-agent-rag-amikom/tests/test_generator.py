import unittest
from app.schemas.evidence import Evidence
from app.generator.prompt_builder import prompt_builder
from app.generator.citation_formatter import citation_formatter
from app.generator.llm import llm_generator
from app.verifier.guardrail import final_verifier

class TestGenerator(unittest.TestCase):
    def setUp(self):
        self.evidence1 = Evidence(
            chunk_id="chunk1",
            source_id="src1",
            title="Pedoman Akademik",
            locator="Bab 2",
            lifecycle="ACTIVE",
            score=0.9,
            chunk_text="Mahasiswa harus lulus minimal 144 SKS.",
            freshness_status="CURRENT"
        )
        
    def test_prompt_builder(self):
        prompt = prompt_builder.build_prompt("berapa sks?", [self.evidence1])
        self.assertIn("144 SKS", prompt)
        
    def test_citation_formatter(self):
        res = citation_formatter.format_citations("Ini jawabannya", [self.evidence1])
        self.assertEqual(res["answer"], "Ini jawabannya")
        self.assertEqual(len(res["citations"]), 1)
        self.assertEqual(res["citations"][0]["source_id"], "src1")
        
    def test_llm_generator(self):
        res = llm_generator.generate("berapa sks?", [self.evidence1])
        self.assertIn("Pedoman Akademik", res["answer"])
        self.assertEqual(len(res["citations"]), 1)
        
    def test_final_verifier_pii(self):
        gen_out = {
            "answer": "KTP saya adalah 1234567890123456.",
            "citations": []
        }
        res = final_verifier.verify(gen_out)
        self.assertIn("[REDACTED]", res["answer"])
        self.assertIn("warning", res)
        
if __name__ == "__main__":
    unittest.main()
