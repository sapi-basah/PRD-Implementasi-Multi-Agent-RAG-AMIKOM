import os
import json
from typing import Dict, Any, Optional, List
from app.config import settings
from app.observability import logger

class ControlRegistry:
    def __init__(self):
        self.control_records: Dict[str, Dict[str, Any]] = {}
        self.conflict_records: Dict[str, Dict[str, Any]] = {}
        self.blocked_records: Dict[str, Dict[str, Any]] = {}
        self.load_registries()

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

    def load_registries(self):
        self._load_jsonl(settings.CONTROL_REGISTRY_PATH, self.control_records)
        self._load_jsonl(settings.CONFLICT_REGISTRY_PATH, self.conflict_records)
        self._load_jsonl(settings.BLOCKED_REGISTRY_PATH, self.blocked_records)

    def get_control_record(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        return self.control_records.get(chunk_id)

    def get_conflict_record_by_id(self, conflict_id: str) -> Optional[Dict[str, Any]]:
        for record in self.conflict_records.values():
            if record.get("conflict_id") == conflict_id:
                return record
        return None

    def get_blocked_record(self, blocker_status: str) -> Optional[Dict[str, Any]]:
        for record in self.blocked_records.values():
            if record.get("blocker_status") == blocker_status:
                return record
        return None

control_registry = ControlRegistry()
