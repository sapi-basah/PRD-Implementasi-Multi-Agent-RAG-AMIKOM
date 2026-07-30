"""E5 query encoder: ONNX inference dengan mean pooling dan L2 normalization."""

import os
from typing import Any

import numpy as np

from app.config.settings import settings
from app.observability import logger
from app.retrieval.service import QueryEncoder

try:
    import onnxruntime as ort
    from transformers import AutoTokenizer

    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logger.warning("onnxruntime or transformers not available.")


class E5QueryEncoder(QueryEncoder):
    """Encoder E5 lokal menggunakan ONNX runtime.

    - Prefix "query: " untuk asymmetric retrieval
    - Mean pooling dengan attention mask
    - L2 normalization
    - Output float32, dimensi 384
    """

    def __init__(self, model_dir: str | None = None):
        self.model_dir = model_dir or settings.E5_MODEL_DIR
        self.session = None
        self.tokenizer = None
        self._load_model()

    def _load_model(self):
        if not ONNX_AVAILABLE:
            return

        onnx_path = os.path.join(self.model_dir, "onnx", "model_int8.onnx")
        if not os.path.exists(onnx_path):
            logger.error(f"E5 ONNX model missing at {onnx_path}")
            return

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_dir, local_files_only=True
            )
            self.session = ort.InferenceSession(
                onnx_path, providers=["CPUExecutionProvider"]
            )
            logger.info("E5 ONNX model and tokenizer loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load E5 model: {e}")

    @property
    def is_available(self) -> bool:
        return self.session is not None and self.tokenizer is not None

    def encode(self, query: str) -> Any:
        if not self.is_available:
            raise RuntimeError("E5 model is not loaded.")

        # E5 requires "query: " prefix for asymmetric tasks
        formatted_query = f"query: {query}"

        inputs = self.tokenizer(
            formatted_query,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="np",
        )

        ort_inputs = {
            "input_ids": inputs["input_ids"].astype(np.int64),
            "attention_mask": inputs["attention_mask"].astype(np.int64),
        }
        if "token_type_ids" in inputs:
            ort_inputs["token_type_ids"] = inputs["token_type_ids"].astype(np.int64)
        else:
            ort_inputs["token_type_ids"] = np.zeros_like(
                inputs["input_ids"], dtype=np.int64
            )

        outputs = self.session.run(None, ort_inputs)
        last_hidden_state = outputs[0]

        # Mean pooling with attention mask
        attention_mask = inputs["attention_mask"]
        input_mask_expanded = np.expand_dims(attention_mask, -1)
        sum_embeddings = np.sum(last_hidden_state * input_mask_expanded, axis=1)
        sum_mask = np.clip(np.sum(input_mask_expanded, axis=1), a_min=1e-9, a_max=None)
        pooled = sum_embeddings / sum_mask

        # L2 Normalization
        norms = np.linalg.norm(pooled, axis=1, keepdims=True)
        norms = np.clip(norms, a_min=1e-9, a_max=None)
        normalized = pooled / norms

        result = normalized[0].astype(np.float32)

        # Validation: no NaN, no Inf, no zero vector
        if np.isnan(result).any() or np.isinf(result).any():
            raise RuntimeError("E5 encoder produced NaN or Inf values")
        if np.allclose(result, 0):
            raise RuntimeError("E5 encoder produced zero vector")
        if result.shape != (384,):
            raise RuntimeError(f"E5 encoder dimension mismatch: {result.shape} != (384,)")

        return result
