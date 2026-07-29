import re

# Out-of-scope keywords based on PRD 5.2 (Keuangan/pembayaran, beasiswa, karier, magang, program studi/cohort lain, dll)
OUT_OF_SCOPE_PATTERNS = [
    re.compile(r'\b(?:spp|bayar|pembayaran|tagihan|keuangan|cicilan|denda)\b', re.IGNORECASE),
    re.compile(r'\b(?:beasiswa|bantuan dana|keringanan spp)\b', re.IGNORECASE),
    re.compile(r'\b(?:karier|karir|lowongan|pekerjaan)\b', re.IGNORECASE),
    re.compile(r'\b(?:magang|internship)\b', re.IGNORECASE),
    re.compile(r'\b(?:sistem informasi|ilmu komunikasi|ekonomi|arsitektur)\b', re.IGNORECASE),
]

def check_out_of_scope(text: str) -> bool:
    """Returns True if the text contains out-of-scope topics."""
    if not isinstance(text, str):
        return False
        
    for pattern in OUT_OF_SCOPE_PATTERNS:
        if pattern.search(text):
            return True
    return False
