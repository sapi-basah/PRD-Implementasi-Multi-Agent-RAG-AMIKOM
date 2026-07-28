import logging
import re
import sys
from app.config import settings

# PII Regex patterns for redaction (NIM, Phone, Email, KTP, Credit Card, Passwords)
PII_PATTERNS = [
    (re.compile(r'\b\d{2}\.\d{2}\.\d{4}\b'), '[REDACTED_NIM]'),  # AMIKOM NIM pattern XX.XX.XXXX
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[REDACTED_EMAIL]'),
    (re.compile(r'\b(?:\+?62|0)8\d{8,11}\b'), '[REDACTED_PHONE]'),
    (re.compile(r'\b\d{16}\b'), '[REDACTED_ID_NUMBER]')
]

def redact_pii(text: str) -> str:
    if not isinstance(text, str):
        return text
    redacted = text
    for pattern, replacement in PII_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted

class PIIRedactingFormatter(logging.Formatter):
    def format(self, record):
        original = super().format(record)
        return redact_pii(original)

def get_logger(name: str = "multi_agent_rag") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
        handler = logging.StreamHandler(sys.stdout)
        formatter = PIIRedactingFormatter('[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = get_logger()
