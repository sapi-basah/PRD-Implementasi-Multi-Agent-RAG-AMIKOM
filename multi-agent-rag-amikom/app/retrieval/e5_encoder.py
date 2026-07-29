import os
import numpy as np
from typing import Any
from app.retrieval.service import QueryEncoder
from app.config import settings
from app.observability import logger

try:
    import onnxruntime as ort
    from transformers import AutoTokenizer
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logger.warning("onnxruntime or transformers not available.")

class E5QueryEncoder(QueryEncoder):
    def __init__(self, model_dir: str = None):
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
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir, local_files_only=True)
            self.session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
            logger.info("E5 ONNX model and tokenizer loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load E5 model: {e}")

    def encode(self, query: str) -> np.ndarray:
        if self.session is None or self.tokenizer is None:
            raise RuntimeError("E5 model is not loaded.")
            
        # E5 requires "query: " prefix for asymmetric tasks
        formatted_query = f"query: {query}"
        
        inputs = self.tokenizer(
            formatted_query, 
            padding=True, 
            truncation=True, 
            max_length=512, 
            return_tensors="np"
        )
        
        ort_inputs = {
            "input_ids": inputs["input_ids"].astype(np.int64),
            "attention_mask": inputs["attention_mask"].astype(np.int64)
        }
        if "token_type_ids" in inputs:
            ort_inputs["token_type_ids"] = inputs["token_type_ids"].astype(np.int64)
        else:
            # If tokenizer doesn't return it but model expects it, create zeros
            ort_inputs["token_type_ids"] = np.zeros_like(inputs["input_ids"], dtype=np.int64)
        
        outputs = self.session.run(None, ort_inputs)
        last_hidden_state = outputs[0]
        
        # Mean pooling
        attention_mask = inputs["attention_mask"]
        input_mask_expanded = np.expand_dims(attention_mask, -1)
        sum_embeddings = np.sum(last_hidden_state * input_mask_expanded, axis=1)
        sum_mask = np.clip(np.sum(input_mask_expanded, axis=1), a_min=1e-9, a_max=None)
        pooled = sum_embeddings / sum_mask
        
        # L2 Normalization
        norms = np.linalg.norm(pooled, axis=1, keepdims=True)
        normalized = pooled / norms
        
        return normalized[0].astype(np.float32)
