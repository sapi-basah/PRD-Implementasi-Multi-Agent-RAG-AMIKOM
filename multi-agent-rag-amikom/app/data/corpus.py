import os
import json
from typing import List, Dict, Any, Optional
from app.config import settings
from app.observability import logger

class ChunkCorpusStore:
    def __init__(self, corpus_path: str = None):
        self.corpus_path = corpus_path or settings.CHUNK_CORPUS_PATH
        self.chunks = {}  # chunk_id -> chunk_data
        self.load_corpus()

    def load_corpus(self):
        if not os.path.exists(self.corpus_path):
            logger.warning(f"Chunk corpus file missing: {self.corpus_path}")
            return
            
        try:
            with open(self.corpus_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    chunk = json.loads(line)
                    if "chunk_id" in chunk:
                        self.chunks[chunk["chunk_id"]] = chunk
            logger.info(f"Loaded {len(self.chunks)} chunks from {self.corpus_path}")
        except Exception as e:
            logger.error(f"Failed to load chunk corpus: {e}")

    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        return self.chunks.get(chunk_id)
        
    def get_all_chunks(self) -> List[Dict[str, Any]]:
        return list(self.chunks.values())
        
chunk_corpus_store = ChunkCorpusStore()
