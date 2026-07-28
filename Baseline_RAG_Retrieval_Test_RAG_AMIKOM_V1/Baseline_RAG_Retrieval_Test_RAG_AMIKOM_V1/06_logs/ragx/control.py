"""Control, guardrail and routing layer executed BEFORE any retrieval.

Every rule below is derived from the CONTROL / CONFLICT / BLOCKED records of
Chunk_Corpus_RAG_AMIKOM_V1 (INT01-INT07, G01, G02, CF001, CF002,
MR-A11-RELATIONS). Gold answers and gold chunk ids are NEVER read here.
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

WIB = dt.timezone(dt.timedelta(hours=7))

# ---------------------------------------------------------------- lexicons ---
OUT_OF_SCOPE_TOPICS = {
    "BEASISWA": [r"\bbeasiswa\b", r"\bscholarship\b", r"\bukt\b"],
    "KEUANGAN": [r"\btagihan\b", r"\bspp\b", r"\bpembayaran\b", r"\bbiaya kuliah\b",
                 r"\bcicilan\b", r"\bdenda\b"],
    "KARIER": [r"\blowongan\b", r"\bkarier\b", r"\bkarir\b", r"\brekrutmen\b",
               r"\bjob fair\b"],
    "MAGANG": [r"\bmagang\b", r"\binternship\b", r"\bmbkm\b"],
}

PII_PAYLOAD = [
    r"\bnim\s*(saya|nya)?\s*[:=]?\s*\d", r"\bnim saya\b", r"\bktp\b", r"\bkartu keluarga\b",
    r"\bakta\b", r"\bno(mor)?\s*(hp|telepon|wa)\b", r"\bnik\b", r"\bpassword\b",
    r"\bnomor rekening\b",
]

PERSONAL_RECORD = [
    r"\b(saya|aku|punyaku|milik saya)\b.*\b(status|jadwal|nilai|transkrip|tagihan|krs|permohonan)\b",
    r"\b(status|jadwal|nilai|transkrip|tagihan|krs|permohonan)\b.*\b(saya|aku|pribadi)\b",
    r"\bcek\b.*\b(status|jadwal|nilai|tagihan)\b",
    r"\bpribadi\b",
]

QUARANTINE_INSTRUCTION = [
    r"ikuti instruksi", r"ikuti perintah", r"menyuruh saya", r"hubungi nomor",
    r"sesuai kata sumber", r"lakukan yang diminta",
]

ARCHIVE_SOURCE_IDS = ["A04", "A05", "D01"]
ARCHIVE_AS_CURRENT = [
    r"\bgunakan\s+(d01|a04|a05)\b", r"\b(d01|a04|a05)\b.*\b(terbaru|current|sekarang|berikutnya)\b",
]

CONFLICT_CF002 = [
    r"\bipk\b.*\b2[.,]0{1,2}\b", r"\b2[.,]0{1,2}\b.*\b(lulus|kelulusan|syarat)\b",
    r"\bipk\b.*\b(minimal|cukup|memenuhi)\b",
]
SUPPRESS_CONFLICT = [r"tidak perlu sebutkan konflik", r"pastikan saja", r"jangan sebut"]

CF001_EQUIVALENCY = [r"\bkode\b.*\b(kurikulum\s*2025|2025)\b", r"\bpenyetaraan\b",
                     r"\bekuivalen\w*\b"]

AMBIGUOUS_RELATION = [r"\bprasyarat\b", r"\bprerequisite\b", r"\bpeta kurikulum\b",
                      r"\bpanah\b", r"\brelasi\b"]

SCHEDULE_INTENT = [
    r"\bkrs\b", r"\bjadwal\b", r"\bagenda\b", r"\bkalender\b", r"\bperiode\b",
    r"\bkapan\b", r"\bujian\b", r"\buts\b", r"\buas\b", r"\bwisuda\b", r"\bregistrasi\b",
    r"\bkuliah\s+(reguler|dimulai|mulai)\b", r"\bbatas\b",
]

ADMIN_INTENT = [
    r"\bsurat\b", r"\bskak\b", r"\bketerangan aktif\b", r"\blegalisir\b", r"\bktm\b",
    r"\bpddikti\b", r"\bcuti\b", r"\bprosedur\b", r"\bmengurus\b", r"\bmengajukan\b",
    r"\bpengajuan\b", r"\bformulir\b", r"\bkrs manual\b", r"\bganti nama\b",
    r"\bmengganti nama\b",
]

ACADEMIC_INTENT = [
    r"\bsks\b", r"\bkurikulum\b", r"\bkonsentrasi\b", r"\bmata kuliah\b", r"\bkode\b",
    r"\bipk\b", r"\blulus\b", r"\bkelulusan\b", r"\bskripsi\b", r"\bprasyarat\b",
    r"\bmasa studi\b", r"\bangkatan\b", r"\bsemester\b", r"\bpenyetaraan\b",
]

# Terms
TERM_RE = re.compile(r"\b(ganjil|genap)\s*(\d{4})\s*/\s*(\d{4})\b", re.I)
CURRENT_ACADEMIC_YEAR = "2025/2026"
# Terms already finished at execution time (WIB 2026-07-27): Genap 2025/2026 and
# everything before it. Ganjil 2026/2027 is the upcoming, unpublished term (G02).
HISTORICAL_TERMS = {("genap", "2025/2026"), ("ganjil", "2025/2026"),
                    ("genap", "2024/2025"), ("ganjil", "2024/2025")}
FUTURE_UNPUBLISHED_TERMS = {("ganjil", "2026/2027")}

HISTORICAL_MARKERS = [r"\bmasih berlaku\b", r"\bdulu\b", r"\blalu\b", r"\bkemarin\b",
                      r"\bsebelumnya\b", r"\barsip\b"]


@dataclass
class ControlDecision:
    response_mode: str = "ANSWER"
    control_triggered: List[str] = field(default_factory=list)
    guardrail_action: str = "NONE"
    handoff_required: bool = False
    handoff_target: str = "NOT_APPLICABLE"
    authentication_required: bool = False
    live_check_required: bool = False
    allow_factual_retrieval: bool = True
    retrieval_mode: str = "CURRENT"          # CURRENT | HISTORICAL
    namespaces: List[str] = field(default_factory=list)
    routing_domain: str = "UNKNOWN"
    expected_agent: str = "UNKNOWN"
    notes: List[str] = field(default_factory=list)
    partial_abstain: List[str] = field(default_factory=list)
    source_constraints: List[str] = field(default_factory=list)


def _any(patterns: List[str], text: str) -> bool:
    return any(re.search(p, text, re.I) for p in patterns)


def _matched(patterns: List[str], text: str) -> List[str]:
    return [p for p in patterns if re.search(p, text, re.I)]


def detect_terms(q: str):
    out = []
    for m in TERM_RE.finditer(q):
        out.append((m.group(1).lower(), f"{m.group(2)}/{m.group(3)}"))
    return out


def route(question: str) -> ControlDecision:
    """Deterministic control + routing decision. No vector search happens here."""
    q = question.lower()
    d = ControlDecision()

    # ---------------------------------------------------------------- domain
    dom = []
    if _any(ACADEMIC_INTENT, q):
        dom.append("ACADEMIC")
    if _any(SCHEDULE_INTENT, q):
        dom.append("SCHEDULE")
    if _any(ADMIN_INTENT, q):
        dom.append("ADMINISTRATION")
    if not dom:
        dom = ["ACADEMIC"]
    d.routing_domain = "+".join(dom)
    ns = []
    if "ACADEMIC" in dom:
        ns.append("active_academic")
    if "SCHEDULE" in dom:
        ns += ["active_schedule", "active_dynamic_schedule"]
    if "ADMINISTRATION" in dom:
        ns += ["active_administration", "active_schedule"]
    # de-dup, keep order
    d.namespaces = list(dict.fromkeys(ns))
    d.expected_agent = {
        "ACADEMIC": "Academic Agent",
        "SCHEDULE": "Schedule Agent",
        "ADMINISTRATION": "Administration Agent",
    }.get(d.routing_domain, "Coordinator Agent")

    # ------------------------------------------------- 1. privacy / PII (INT07)
    pii_payload = _any(PII_PAYLOAD, q)
    personal = _any(PERSONAL_RECORD, q)
    oos_topic = None
    for topic, pats in OUT_OF_SCOPE_TOPICS.items():
        if _any(pats, q):
            oos_topic = topic
            break

    if pii_payload or (personal and oos_topic):
        d.response_mode = "REFUSE"
        d.control_triggered.append("INT07")
        d.guardrail_action = (
            "BLOCK_PII_AND_REDIRECT" if pii_payload else "BLOCK_OUT_OF_SCOPE_PII"
        )
        d.handoff_required = True
        d.handoff_target = "Kanal resmi terautentikasi"
        d.authentication_required = True
        d.allow_factual_retrieval = False
        d.notes.append("PII payload / personal out-of-scope record request refused.")
        return d

    if oos_topic:
        d.response_mode = "REFUSE"
        d.control_triggered.append("INT07")
        d.control_triggered.append(f"OUT_OF_SCOPE:{oos_topic}")
        d.guardrail_action = (
            "BLOCK_FINANCIAL_PII" if oos_topic == "KEUANGAN" else "BLOCK_OUT_OF_SCOPE"
        )
        if _any(QUARANTINE_INSTRUCTION, q) or _any([r"\blowongan\b"], q):
            d.control_triggered.append("INT05")
            d.guardrail_action = "BLOCK_QUARANTINED_SOURCE"
        d.handoff_required = True
        d.handoff_target = {
            "BEASISWA": "Bagian Kemahasiswaan",
            "KEUANGAN": "DPK / dashboard terautentikasi",
            "KARIER": "BPC",
            "MAGANG": "Program Studi / BPC",
        }[oos_topic]
        d.live_check_required = oos_topic in ("BEASISWA", "KARIER")
        d.allow_factual_retrieval = False
        d.notes.append(f"Scope freeze: {oos_topic} is out of MVP scope.")
        return d

    if personal:
        d.response_mode = "ESCALATE"
        d.control_triggered.append("INT07")
        d.guardrail_action = "BLOCK_PERSONAL_DATA_ACCESS"
        d.handoff_required = True
        d.handoff_target = "Kanal/dashboard terautentikasi"
        d.authentication_required = True
        d.live_check_required = True
        d.allow_factual_retrieval = False
        d.notes.append("Personal record lookup is outside system capability.")
        return d

    # --------------------------------------- 2. quarantine / source poisoning
    if _any(QUARANTINE_INSTRUCTION, q):
        d.response_mode = "REFUSE"
        d.control_triggered.append("INT05")
        d.guardrail_action = "BLOCK_SOURCE_POISONING"
        d.allow_factual_retrieval = False
        d.notes.append("Instructions embedded in corpus sources are never executed.")
        return d

    # ----------------------------------------------- 3. archive used as current
    if _any(ARCHIVE_AS_CURRENT, q):
        d.response_mode = "ABSTAIN"
        d.control_triggered.append("INT05")
        d.guardrail_action = "BLOCK_ARCHIVE_AS_CURRENT"
        d.handoff_required = True
        d.handoff_target = "DAAK"
        d.live_check_required = True
        d.allow_factual_retrieval = False
        d.notes.append("ARCHIVE lifecycle can never answer a current question.")
        return d

    # ------------------------------------------------------ 4. CF002 conflict
    if _any(CONFLICT_CF002, q):
        d.response_mode = "ESCALATE"
        d.control_triggered += ["CF002", "INT06"]
        d.handoff_required = True
        d.handoff_target = "Program Studi Informatika / FIK"
        if _any(SUPPRESS_CONFLICT, q):
            d.guardrail_action = "SURFACE_CONFLICT"
            d.notes.append("Refused request to hide an OPEN conflict.")
        d.allow_factual_retrieval = True   # supporting procedure text may still help
        d.source_constraints.append("CF002_OPEN_DO_NOT_RESOLVE")
        d.notes.append("CF002 is an OPEN accepted blocker: never synthesise a value.")
        # continue - a second intent may still be answerable

    # ------------------------------------------- 5. temporal routing / G02 / G01
    terms = detect_terms(question)
    schedule_like = _any(SCHEDULE_INTENT, q)
    if terms:
        hist = [t for t in terms if t in HISTORICAL_TERMS]
        fut = [t for t in terms if t in FUTURE_UNPUBLISHED_TERMS]
        validity_question = _any(
            [r"\bmasih berlaku\b", r"\bberlaku\b", r"\bvalid\b", r"\bboleh dipakai\b"], q
        )
        conjunction = bool(re.search(r"\bdan\b|\bserta\b", q)) or q.count("?") > 1
        if fut:
            d.control_triggered.append("G02")
            d.handoff_required = True
            d.handoff_target = "DAAK"
            d.live_check_required = True
            d.partial_abstain.append(
                "Agenda/KRS " + " ".join(f"{a.title()} {b}" for a, b in fut)
            )
            if validity_question:
                # lifecycle validity question, answerable from INT05 + archive metadata
                d.response_mode = "ANSWER"
                d.control_triggered.append("INT05")
                d.notes.append(
                    "Lifecycle validity question: answer from lifecycle metadata, "
                    "no date is invented for the unpublished term."
                )
            elif conjunction and (_any(ACADEMIC_INTENT, q) or _any(ADMIN_INTENT, q)):
                d.response_mode = "ANSWER"   # partial answer + partial abstain
                d.notes.append("Multi-intent: answer factual part, abstain on G02 part.")
            else:
                d.response_mode = "ABSTAIN"
                d.allow_factual_retrieval = False
                d.notes.append("G02 OPEN blocker: no factual retrieval for the date.")
        if hist:
            d.retrieval_mode = "HISTORICAL"
            d.namespaces = ["archive_schedule"]
            d.control_triggered.append("INT05")
            d.notes.append("Historical term detected: ARCHIVE namespace only.")
            if _any(ADMIN_INTENT, q) or (conjunction and _any(ACADEMIC_INTENT, q)):
                # multi-intent: historical schedule part + current procedural part
                extra = []
                if _any(ADMIN_INTENT, q):
                    extra.append("active_administration")
                if conjunction and _any(ACADEMIC_INTENT, q):
                    extra.append("active_academic")
                d.namespaces = ["archive_schedule"] + extra
                d.retrieval_mode = "MIXED"
                d.notes.append("MIXED filter: archive for the historical sub-intent, "
                               "current namespace for the procedural sub-intent.")
    elif schedule_like and not _any(ADMIN_INTENT, q) and re.search(r"\bkapan\b", q):
        # schedule question with no term at all -> cannot resolve the period
        d.response_mode = "ASK_CONTEXT"
        d.control_triggered += ["G02", "G01"]
        d.handoff_required = True
        d.handoff_target = "DAAK"
        d.live_check_required = True
        d.notes.append("Term not specified: ask for the semester before answering.")
    elif schedule_like and re.search(r"\b(berikutnya|terbaru|selanjutnya|mendatang)\b", q):
        d.response_mode = "ASK_CONTEXT"
        d.control_triggered += ["G02", "G01"]
        d.handoff_required = True
        d.handoff_target = "DAAK"
        d.live_check_required = True
        d.notes.append("Relative period ('berikutnya'): ask context, abstain on G02.")
    elif schedule_like and re.search(r"\bkapan\b", q) and _any(ADMIN_INTENT, q):
        d.response_mode = "ASK_CONTEXT"
        d.control_triggered += ["G02"]
        d.handoff_required = True
        d.handoff_target = "DAAK"
        d.live_check_required = True
        d.notes.append("Procedure timing depends on an unpublished calendar.")

    # -------------------------------------------------------------- 6. CF001
    if _any(CF001_EQUIVALENCY, q):
        d.control_triggered.append("CF001")
        d.source_constraints.append("A12_EXPLICIT_ROWS_ONLY")
        d.notes.append("CF001 RESOLVED: A12 explicit equivalency rows, A10 for 2025 facts.")

    # ------------------------------------------------- 7. MR-A11-RELATIONS
    if _any(AMBIGUOUS_RELATION, q):
        d.control_triggered.append("MR-A11-RELATIONS")
        d.source_constraints.append("A10_PRASYARAT_COLUMN_AUTHORITATIVE")
        d.notes.append("Ambiguous A11 arrows must not be inferred.")

    # ------------------------------------------------------- 8. G01 freshness
    if schedule_like or "active_dynamic_schedule" in d.namespaces:
        d.control_triggered.append("G01")
        d.live_check_required = True

    if _any(ADMIN_INTENT, q) and re.search(
        r"\b(unggah|upload|kirim|ajukan|mengajukan|mengurus|legalisir|skak|ktm|pddikti)\b", q
    ):
        d.handoff_required = True
        if d.handoff_target == "NOT_APPLICABLE":
            d.handoff_target = "Kanal resmi terautentikasi"
        d.authentication_required = True

    # ---------------------------------------------------- 9. G02 retrieval ban
    # Section 4 of the brief: when G02 is triggered no factual retrieval may be
    # performed for the blocked (schedule) sub-intent. For a multi-intent query the
    # answerable sub-intent keeps its own namespace, the schedule namespaces are
    # dropped so no date can leak into the context.
    if "G02" in d.control_triggered and d.retrieval_mode == "CURRENT":
        pruned = [n for n in d.namespaces
                  if n not in ("active_schedule", "active_dynamic_schedule")]
        if pruned and pruned != d.namespaces:
            d.namespaces = pruned
            d.notes.append("G02: schedule namespaces removed from the candidate filter.")
        elif not pruned:
            d.allow_factual_retrieval = False
            d.notes.append("G02: only a schedule intent present -> no factual retrieval.")

    d.control_triggered = list(dict.fromkeys(d.control_triggered))
    return d


def freshness_check(rec, now: Optional[dt.datetime] = None) -> Dict[str, Any]:
    """G01 / ACTIVE_DYNAMIC freshness evaluation."""
    now = now or dt.datetime.now(WIB)
    res = {"expired": False, "age_days": None, "ttl_days": rec.ttl_days,
           "response_mode": "NORMAL"}
    snap = rec.snapshot_at_wib
    if not snap or snap == "NOT_APPLICABLE":
        if rec.lifecycle_status == "ACTIVE_DYNAMIC":
            res["expired"] = True
            res["response_mode"] = "LIVE_CHECK_OR_ABSTAIN"
        return res
    try:
        ts = dt.datetime.fromisoformat(snap)
    except ValueError:
        return res
    age = (now - ts).total_seconds() / 86400.0
    res["age_days"] = round(age, 3)
    try:
        ttl = float(rec.ttl_days)
    except (TypeError, ValueError):
        ttl = None
    if ttl is not None and age > ttl:
        res["expired"] = True
        res["response_mode"] = "LIVE_CHECK_OR_ABSTAIN"
    elif rec.lifecycle_status == "ACTIVE_DYNAMIC" or int(rec.live_check_required or 0):
        res["response_mode"] = "LIVE_CHECK"
    return res
