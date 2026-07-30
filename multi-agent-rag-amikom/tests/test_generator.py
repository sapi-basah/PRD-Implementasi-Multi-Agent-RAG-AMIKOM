import unittest
from app.schemas import Evidence, Citation
from app.generator.prompt_builder import prompt_builder
from app.generator.citation_formatter import citation_formatter, citation_verifier
from app.generator.llm import llm_generator
from app.verifier.guardrail import final_verifier


class TestGenerator(unittest.TestCase):
    def setUp(self):
        self.evidence1 = Evidence(
            chunk_id="chunk1",
            source_id="src1",
            title="Pedoman Akademik",
            locator="Bab 2",
            retrieval_namespace="active_academic",
            lifecycle_status="ACTIVE",
            score=0.9,
            chunk_text="Mahasiswa harus lulus minimal 144 SKS.",
            freshness_status="CURRENT",
        )

    def test_prompt_builder(self):
        prompt = prompt_builder.build_prompt("berapa sks?", [self.evidence1])
        self.assertIn("144 SKS", prompt)
        self.assertIn("chunk1", prompt)
        self.assertIn("src1", prompt)

    def test_citation_formatter(self):
        res = citation_formatter.format_citations("Ini jawabannya", [self.evidence1])
        self.assertEqual(res["answer"], "Ini jawabannya")
        self.assertEqual(len(res["citations"]), 1)
        self.assertEqual(res["citations"][0]["source_id"], "src1")

    def test_citation_verifier(self):
        raw_cits = [{"source_id": "src1", "chunk_id": "chunk1", "locator": "Bab 2"}]
        verified = citation_verifier.build_citations(raw_cits, [self.evidence1])
        self.assertEqual(len(verified), 1)
        self.assertEqual(verified[0].chunk_id, "chunk1")

    def test_llm_generator(self):
        res = llm_generator.generate("berapa sks?", [self.evidence1])
        self.assertIn("answer", res)
        self.assertIn("citations", res)
        self.assertIn("144 SKS", res["answer"])

    def test_final_verifier_agent_result(self):
        from app.schemas import AgentResult
        agent_res = AgentResult(
            agent="AcademicAgent",
            evidence=[self.evidence1],
        )
        ver = final_verifier.verify_agent_result(agent_res, temporal_mode="CURRENT")
        self.assertIn(ver.status, ["PASS", "FAIL"])

    def test_final_verifier_pii_in_output(self):
        citations = [Citation(source_id="src1", chunk_id="chunk1", locator="Bab 2")]
        ver = final_verifier.verify_final_response(
            "KTP saya adalah 1234567890123456.",
            citations,
            [self.evidence1],
        )
        pii_checks = [c for c in ver.checks if c.check_name == "pii_in_output"]
        self.assertGreater(len(pii_checks), 0)

    def test_pii_redaction(self):
        redacted = final_verifier.redact_pii_from_output("KTP 1234567890123456")
        self.assertIn("[REDACTED", redacted)
        self.assertNotIn("1234567890123456", redacted)

    def test_evidence_selector_v2_abstain(self):
        res = llm_generator.generate("test", [], response_mode="ABSTAIN")
        self.assertEqual(res["generation_backend"], "EVIDENCE_SELECTOR_V2")
        self.assertIn("belum tersedia", res["answer"])


if __name__ == "__main__":
    unittest.main()
