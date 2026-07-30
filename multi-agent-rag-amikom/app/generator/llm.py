"""LLM Generator: provider-agnostic LLM interface dengan Evidence Selector V2 fallback.

- Provider/model/key seluruhnya melalui environment
- Temperature 0 untuk evaluasi
- Output JSON terstruktur dan divalidasi
- Prompt melarang penambahan fakta baru
- Evidence Selector V2 sebagai fallback deterministik
"""

import json
from typing import Any, Dict, List, Optional

from app.config.settings import settings
from app.generator.citation_formatter import citation_verifier
from app.generator.prompt_builder import prompt_builder
from app.observability import logger
from app.schemas import Citation, Evidence


class LLMGenerator:
    """Provider-agnostic LLM generator."""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self._client = None
        self._init_client()

    def _init_client(self):
        """Initialize LLM client berdasarkan provider."""
        if self.provider in ("mock", "", "replace_me"):
            logger.info("LLM provider: mock/not configured. Using Evidence Selector V2 as primary.")
            return

        try:
            if self.provider in ("openai", "groq", "openrouter"):
                import openai

                base_urls = {
                    "openai": "https://api.openai.com/v1",
                    "groq": "https://api.groq.com/openai/v1",
                    "openrouter": "https://openrouter.ai/api/v1",
                }
                self._client = openai.OpenAI(
                    api_key=settings.LLM_API_KEY,
                    base_url=base_urls.get(self.provider, "https://api.openai.com/v1"),
                )
                logger.info(f"LLM client initialized: provider={self.provider}, model={self.model}")
            else:
                logger.warning(f"Unknown LLM provider: {self.provider}. Using Evidence Selector V2.")
        except ImportError:
            logger.warning("openai package not installed. Using Evidence Selector V2.")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")

    @property
    def is_available(self) -> bool:
        return self._client is not None

    @property
    def backend_name(self) -> str:
        if self.is_available:
            return f"LLM_{self.provider.upper()}"
        return "EVIDENCE_SELECTOR_V2"

    def generate(
        self,
        query: str,
        evidence: List[Evidence],
        response_mode: str = "ANSWER",
    ) -> Dict[str, Any]:
        """Generate jawaban dari evidence.

        Jika LLM tersedia, gunakan LLM. Jika tidak, gunakan Evidence Selector V2.
        """
        # Try LLM first
        if self.is_available and response_mode == "ANSWER" and evidence:
            try:
                return self._generate_with_llm(query, evidence)
            except Exception as e:
                logger.error(f"LLM generation failed: {e}. Falling back to Evidence Selector V2.")

        # Fallback: Evidence Selector V2
        return self._evidence_selector_v2(query, evidence, response_mode)

    def _generate_with_llm(self, query: str, evidence: List[Evidence]) -> Dict[str, Any]:
        """Generate menggunakan LLM provider."""
        prompt = prompt_builder.build_prompt(query, evidence)

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt_builder.system_prompt()},
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            max_tokens=1024,
        )

        raw_text = response.choices[0].message.content or ""

        # Try to parse as JSON
        try:
            parsed = json.loads(raw_text)
            answer = parsed.get("answer", raw_text)
            raw_citations = parsed.get("citations", [])
        except (json.JSONDecodeError, TypeError):
            answer = raw_text
            raw_citations = []

        # Build citations from evidence
        citations = citation_verifier.build_citations(raw_citations, evidence)

        return {
            "answer": answer,
            "citations": citations,
            "generation_backend": f"LLM_{self.provider.upper()}",
        }

    def _evidence_selector_v2(
        self,
        query: str,
        evidence: List[Evidence],
        response_mode: str = "ANSWER",
    ) -> Dict[str, Any]:
        """Evidence Selector V2: fallback deterministik.

        Hanya mengekstrak atau merangkum evidence retrieval.
        Tidak menggunakan expected answer atau gold answer.
        Label: generation_backend=EVIDENCE_SELECTOR_V2
        """
        if response_mode != "ANSWER" or not evidence:
            # Non-answer modes
            mode_messages = {
                "ABSTAIN": "Maaf, informasi yang Anda tanyakan belum tersedia dalam sistem.",
                "ESCALATE": "Pertanyaan ini memerlukan eskalasi ke pihak berwenang.",
                "HANDOFF": "Silakan hubungi unit terkait untuk informasi lebih lanjut.",
                "REFUSE": "Pertanyaan ini di luar cakupan layanan sistem.",
                "ASK_CONTEXT": "Mohon berikan konteks tambahan untuk menjawab pertanyaan Anda.",
                "LIVE_CHECK_OR_ABSTAIN": "Informasi ini memerlukan pengecekan langsung ke sumber resmi.",
                "ERROR": "Terjadi kesalahan dalam pemrosesan.",
            }
            return {
                "answer": mode_messages.get(response_mode, "Tidak ada informasi yang ditemukan."),
                "citations": [],
                "generation_backend": "EVIDENCE_SELECTOR_V2",
            }

        # Build answer from evidence
        top_evidence = evidence[:5]
        parts = []
        citations: List[Dict[str, str]] = []

        for i, ev in enumerate(top_evidence):
            if ev.chunk_text:
                # Extract first meaningful sentence(s)
                text = ev.chunk_text.strip()
                if len(text) > 300:
                    text = text[:300] + "..."
                parts.append(f"[{i+1}] {text}")
                citations.append({
                    "source_id": ev.source_id,
                    "chunk_id": ev.chunk_id,
                    "locator": ev.locator,
                })

        answer = (
            f"Berdasarkan informasi yang tersedia:\n\n"
            + "\n\n".join(parts)
        )

        verified_citations = citation_verifier.build_citations(citations, evidence)

        return {
            "answer": answer,
            "citations": verified_citations,
            "generation_backend": "EVIDENCE_SELECTOR_V2",
        }


llm_generator = LLMGenerator()
