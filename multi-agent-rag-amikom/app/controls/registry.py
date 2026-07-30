"""Control registry: memuat dan menyediakan akses ke control, conflict, dan blocked registries."""

import json
import os
from typing import Any, Dict, List, Optional

from app.config.settings import settings
from app.observability import logger


class ControlRegistry:
    """Registry untuk chunk_control, chunk_conflict_verifier, dan chunk_blocked_verifier."""

    def __init__(self):
        self.control_records: Dict[str, Dict[str, Any]] = {}
        self.conflict_records: Dict[str, Dict[str, Any]] = {}
        self.blocked_records: Dict[str, Dict[str, Any]] = {}
        self._conflict_by_id: Dict[str, Dict[str, Any]] = {}
        self._load_registries()

    def _load_jsonl(self, path: str, target_dict: Dict[str, Dict[str, Any]]):
        if not os.path.exists(path):
            logger.warning(f"Registry file missing: {path}")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    if "chunk_id" in record:
                        target_dict[record["chunk_id"]] = record
            logger.info(f"Loaded {len(target_dict)} records from {path}")
        except Exception as e:
            logger.error(f"Failed to load registry {path}: {e}")

    def _load_registries(self):
        self._load_jsonl(settings.CONTROL_REGISTRY_PATH, self.control_records)
        self._load_jsonl(settings.CONFLICT_REGISTRY_PATH, self.conflict_records)
        self._load_jsonl(settings.BLOCKED_REGISTRY_PATH, self.blocked_records)

        # Index conflict records by conflict_id
        for record in self.conflict_records.values():
            cid = record.get("conflict_id")
            if cid:
                self._conflict_by_id[cid] = record

    def get_control_record(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        return self.control_records.get(chunk_id)

    def is_chunk_blocked(self, chunk_id: str) -> bool:
        return chunk_id in self.blocked_records

    def get_blocked_record(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        return self.blocked_records.get(chunk_id)

    def is_chunk_conflicted(self, chunk_id: str) -> bool:
        return chunk_id in self.conflict_records

    def get_conflict_record(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        return self.conflict_records.get(chunk_id)

    def get_conflict_by_id(self, conflict_id: str) -> Optional[Dict[str, Any]]:
        return self._conflict_by_id.get(conflict_id)

    def get_all_blocked_chunk_ids(self) -> List[str]:
        return list(self.blocked_records.keys())

    def get_all_conflict_chunk_ids(self) -> List[str]:
        return list(self.conflict_records.keys())


control_registry = ControlRegistry()
