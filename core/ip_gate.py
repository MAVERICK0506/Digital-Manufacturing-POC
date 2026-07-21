"""
IP Validation Gate — Step 2 of the official workflow.

HONEST SCOPE: this checks file type, filename scope, and basic integrity.
It does NOT do deep IP-content inspection (e.g. detecting extra proprietary geometry
hidden inside a STEP file) — that requires CAD-format-specific parsing tooling and is
a known, explicitly flagged gap (see architecture doc Part D.1 discussion).
"""

import os

ALLOWED_EXTENSIONS = {
    "MBD":  {".stp", ".step", ".prt", ".pdf"},   # .pdf allowed for drawing-derived MBD stand-ins
    "MBOM": {".xlsx", ".csv", ".pdf"},
    "NC":   {".nc", ".tap", ".txt", ".gcode"},
    "SOP":  {".pdf", ".docx"},
}

# Agreed POC scope — extend as real part numbers are confirmed with the team
AGREED_PART_NUMBERS = {
    "02736321", "00158794", "00234408", "00157317", "00229454", "00161535",
    "00157359", "00155366", "00157370", "03213883", "00158788", "00158753",
    "00168967", "00157303", "03213886", "00158735", "00158572", "03210002",
    "00157349", "00231540", "00157376", "00158576", "00158585", "00156867",
    "00158897", "00168356", "00160836", "00168876",
}


class ValidationResult:
    def __init__(self, passed: bool, reason_code: str = None, detail: str = None):
        self.passed = passed
        self.reason_code = reason_code
        self.detail = detail

    def __repr__(self):
        return f"ValidationResult(passed={self.passed}, reason_code={self.reason_code}, detail={self.detail!r})"


def validate(filepath: str, declared_doc_type: str, declared_part_no: str = None) -> ValidationResult:
    """Runs the 3 implemented layers: type whitelist, scope match, integrity."""

    # Layer 1 — sanity / integrity
    if not os.path.isfile(filepath):
        return ValidationResult(False, "CORRUPT_OR_INVALID", "File does not exist")
    if os.path.getsize(filepath) == 0:
        return ValidationResult(False, "CORRUPT_OR_INVALID", "File is empty (0 bytes)")

    # Layer 2 — file type whitelist
    ext = os.path.splitext(filepath)[1].lower()
    allowed = ALLOWED_EXTENSIONS.get(declared_doc_type.upper())
    if allowed is None:
        return ValidationResult(False, "OUT_OF_SCOPE", f"Unknown doc_type '{declared_doc_type}'")
    if ext not in allowed:
        return ValidationResult(
            False, "TYPE_MISMATCH",
            f"Extension '{ext}' not allowed for doc_type '{declared_doc_type}' (allowed: {allowed})"
        )

    # Layer 3 — scope match against agreed part list (skipped if part_no not yet known/declared)
    if declared_part_no and declared_part_no not in AGREED_PART_NUMBERS:
        return ValidationResult(
            False, "OUT_OF_SCOPE",
            f"Part number '{declared_part_no}' not in agreed POC scope"
        )

    return ValidationResult(True)
