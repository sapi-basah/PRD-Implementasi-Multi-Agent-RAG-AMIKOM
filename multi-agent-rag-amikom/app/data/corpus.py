"""Corpus store: akses chunk corpus JSONL."""

import json
import os
from typing import Any, Dict, List, Optional

from app.config.settings import settings
from app.observability import logger


class ChunkCorpusStore:
    """Memuat dan menyediakan akses ke chunk corpus JSONL."""

    def __init__(self, corpus_path: str | None = None):
        self.corpus_path = corpus_path or settings.CHUNK_CORPUS_PATH
        self.chunks: Dict[str, Dict[str, Any]] = {}
        self._load_corpus()

    def _load_corpus(self):
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

    def get_chunks_by_source(self, source_id: str) -> List[Dict[str, Any]]:
        return [c for c in self.chunks.values() if c.get("source_id") == source_id]


chunk_corpus_store = ChunkCorpusStore()
