from typing import List, Dict, Any
from app.schemas.evidence import Evidence

class PromptBuilder:
    def build_prompt(self, query: str, evidences: List[Evidence]) -> str:
        prompt = (
            "Anda adalah asisten akademik S1 Informatika Universitas AMIKOM Yogyakarta.\n"
            "Gunakan konteks berikut untuk menjawab pertanyaan pengguna.\n"
            "Jika jawaban tidak ada di konteks, katakan bahwa Anda tidak tahu, "
            "jangan mengarang informasi.\n\n"
            "Konteks:\n"
        )
        
        for i, ev in enumerate(evidences):
            prompt += f"[{i+1}] {ev.chunk_text}\n"
            
        prompt += f"\nPertanyaan: {query}\n"
        prompt += "Jawaban:\n"
        return prompt

prompt_builder = PromptBuilder()
