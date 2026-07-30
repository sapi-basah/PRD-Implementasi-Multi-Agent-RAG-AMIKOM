"""Prompt builder untuk LLM generation.

Prompt contract:
- Tidak menambahkan fakta baru
- Tidak menggunakan pengetahuan umum di luar evidence
- Tidak membuat tanggal, prosedur, sumber, atau locator
"""

from typing import List

from app.schemas import Evidence


class PromptBuilder:
    """Build structured prompt untuk LLM dari evidence."""

    @staticmethod
    def system_prompt() -> str:
        return (
            "Anda adalah asisten akademik resmi S1 Informatika Universitas AMIKOM Yogyakarta.\n\n"
            "ATURAN KETAT:\n"
            "1. Jawab HANYA berdasarkan konteks/evidence yang diberikan.\n"
            "2. JANGAN menambahkan fakta, tanggal, prosedur, atau informasi yang TIDAK ada dalam konteks.\n"
            "3. JANGAN menggunakan pengetahuan umum di luar evidence yang disediakan.\n"
            "4. JANGAN membuat source_id, chunk_id, atau locator baru.\n"
            "5. Setiap klaim faktual HARUS memiliki citation [nomor] yang merujuk ke evidence.\n"
            "6. Jika informasi tidak ada dalam konteks, katakan bahwa Anda tidak memiliki informasi tersebut.\n"
            "7. Gunakan bahasa Indonesia yang formal dan jelas.\n\n"
            "FORMAT OUTPUT (JSON):\n"
            '{\n'
            '  "answer": "Teks jawaban dengan citation [1], [2], dst.",\n'
            '  "citations": [\n'
            '    {"source_id": "...", "chunk_id": "...", "locator": "..."}\n'
            '  ]\n'
            '}\n'
        )

    def build_prompt(self, query: str, evidence: List[Evidence]) -> str:
        prompt = "KONTEKS EVIDENCE:\n\n"

        for i, ev in enumerate(evidence):
            prompt += (
                f"[{i+1}] source_id={ev.source_id} | chunk_id={ev.chunk_id} | "
                f"locator={ev.locator} | namespace={ev.retrieval_namespace} | "
                f"lifecycle={ev.lifecycle_status}\n"
                f"{ev.chunk_text}\n\n"
            )

        prompt += f"PERTANYAAN: {query}\n\n"
        prompt += "Jawab dalam format JSON sesuai aturan di atas.\n"
        return prompt


prompt_builder = PromptBuilder()
