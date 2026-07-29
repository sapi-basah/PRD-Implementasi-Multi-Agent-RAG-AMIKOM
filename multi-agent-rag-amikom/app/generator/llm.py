
from typing import List, Dict, Any
from app.schemas.evidence import Evidence
from app.generator.prompt_builder import prompt_builder
from app.generator.citation_formatter import citation_formatter
from app.observability import logger

class MockLLMGenerator:
    def generate(self, query: str, evidences: List[Evidence]) -> Dict[str, Any]:
        prompt = prompt_builder.build_prompt(query, evidences)
        logger.info("Generating response with LLM...")
        
        if not evidences:
            answer = "Maaf, saya tidak menemukan informasi yang relevan di sistem."
        else:
            answer = f"Berdasarkan informasi yang ditemukan, {evidences[0].title} menyebutkan bahwa {evidences[0].chunk_text[:100]}..."
            
        return citation_formatter.format_citations(answer, evidences)

llm_generator = MockLLMGenerator()
