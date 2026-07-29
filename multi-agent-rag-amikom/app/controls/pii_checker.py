import re

# PII Regex patterns for redaction (NIM, Phone, Email, KTP, Credit Card, Passwords)
PII_PATTERNS = [
    (re.compile(r'\b\d{2}\.\d{2}\.\d{4}\b'), 'NIM'),  # AMIKOM NIM pattern XX.XX.XXXX
    (re.compile(r'\b\d{2}[Xx]{4,}\b'), 'NIM_MASK'), # Masked NIM 25XXXX
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), 'EMAIL'),
    (re.compile(r'\b(?:\+?62|0)8\d{8,11}\b'), 'PHONE'),
    (re.compile(r'\b\d{16}\b'), 'ID_NUMBER')
]

def check_pii(text: str) -> bool:
    """Returns True if PII is detected in the text, False otherwise."""
    if not isinstance(text, str):
        return False
        
    for pattern, _ in PII_PATTERNS:
        if pattern.search(text):
            return True
    return False
