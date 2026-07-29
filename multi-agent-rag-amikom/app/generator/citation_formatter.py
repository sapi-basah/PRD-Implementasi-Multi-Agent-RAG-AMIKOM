from typing import List, Dict, Any
from app.schemas.evidence import Evidence

class CitationFormatter:
    def format_citations(self, response_text: str, evidences: List[Evidence]) -> Dict[str, Any]:
        """
        In a real system, we would match citations like [1] to the evidence list.
        For now, we simply append the sources used.
        """
        citations = []
        for ev in evidences:
            citations.append({
                "source_id": ev.source_id,
                "title": ev.title,
                "locator": ev.locator
            })
            
        return {
            "answer": response_text,
            "citations": citations
        }

citation_formatter = CitationFormatter()
