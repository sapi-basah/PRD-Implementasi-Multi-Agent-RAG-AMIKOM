import os
import hashlib
from typing import Dict, Any
from app.config import settings

EXPECTED_HASHES = {
    "config.json": "cb99455288675345e1a4f411438d5d0adbba5fbd3a67ea4fb03c015433b996c1",
    "tokenizer.json": "0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39",
    "tokenizer_config.json": "a1d6bc8734a6f635dc158508bef000f8e2e5a759c7d92f984b2c86e5ff53425b",
    "onnx/model_int8.onnx": "4d24e2bc01a447951524466ef533e52944bf48509e6552810bcee1a2711cb02c"
}

def verify_e5_model(model_dir: str = None) -> Dict[str, Any]:
    """Verify E5 model files and their hashes to clear the Retrieval Gate."""
    dir_path = model_dir or settings.E5_MODEL_DIR
    
    result = {
        "status": "PASS",
        "missing_files": [],
        "hash_mismatches": []
    }
    
    for filename, expected_hash in EXPECTED_HASHES.items():
        filepath = os.path.join(dir_path, filename)
        if not os.path.exists(filepath):
            result["status"] = "FAIL"
            result["missing_files"].append(filename)
            continue
            
        # Check hash
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            actual_hash = sha256_hash.hexdigest()
            if actual_hash != expected_hash:
                result["status"] = "FAIL"
                result["hash_mismatches"].append({
                    "file": filename,
                    "expected": expected_hash,
                    "actual": actual_hash
                })
        except Exception:
            result["status"] = "FAIL"
            result["missing_files"].append(filename)
            
    return result
