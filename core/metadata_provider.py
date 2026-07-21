"""
MetadataProvider — extracts structured metadata from a file, keyed by doc_type.

STATUS PER DOC TYPE (as of this build):
  MBD/Drawing : VALIDATED against real Weatherford field structure
                (Part Number / Model File / Model Version / Drawing File / Drawing Version)
  MBOM        : VALIDATED against real Weatherford BOM column structure
                (Line Number / Number / Primary Legacy Number / Name / Quantity / UOM / ...)
  SOP         : PLACEHOLDER — no real Weatherford SOP sample received yet. Generic filename-based
                extraction only. MUST be revisited once a real sample arrives.
  NC          : PLACEHOLDER — no real Weatherford NC program sample received yet. Generic
                filename-based extraction only. MUST be revisited once a real sample arrives.

Production note: once Windchill metadata API access exists, this whole module is largely
replaced by a WindchillMetadataProvider that maps Windchill's native fields onto this same
output shape — see architecture doc Part D.1.
"""

import os
import re
import pandas as pd


# ---- Filename pattern: expects PARTNO_DOCTYPE_RevX.ext, e.g. "02736321_MBOM_RevD.pdf" ----
FILENAME_PATTERN = re.compile(
    r"(?P<part_no>[A-Za-z0-9\-]+)_(?P<doc_type>MBD|MBOM|NC|SOP)_Rev(?P<revision>[A-Za-z0-9.]+?)"
    r"(?:\.[A-Za-z0-9]+)?$",
    re.IGNORECASE,
)


def extract_from_filename(filename: str) -> dict:
    """Fallback / first-pass extraction: pull part_no, doc_type, revision straight from filename."""
    match = FILENAME_PATTERN.search(filename)
    if match:
        return {
            "part_no": match.group("part_no"),
            "doc_type": match.group("doc_type").upper(),
            "revision": match.group("revision"),
        }
    return {"part_no": None, "doc_type": None, "revision": None}


def extract_mbom_metadata(xlsx_or_csv_path: str) -> list:
    """
    VALIDATED against real Weatherford MBOM/eBOM structure (see 02736321 BOM PDF sample):
    columns: Line Number, Number, Primary Legacy Number, Name, Quantity, UOM,
             Find Number, Reference Designator.

    Returns a list of dicts, one per BOM line — ready to feed into Parts + Relationships tables.
    """
    if xlsx_or_csv_path.lower().endswith(".csv"):
        df = pd.read_csv(xlsx_or_csv_path)
    else:
        df = pd.read_excel(xlsx_or_csv_path)

    # normalize expected column names (real Weatherford BOM headers)
    df.columns = [c.strip() for c in df.columns]
    required = ["Number", "Name", "Quantity", "UOM"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"MBOM file missing expected columns: {missing}. Found: {list(df.columns)}")

    lines = []
    for _, row in df.iterrows():
        lines.append({
            "part_no": str(row["Number"]).strip(),
            "name": str(row["Name"]).strip(),
            "qty": row["Quantity"],
            "uom": row["UOM"],
        })
    return lines


def extract_mbd_metadata(title_block: dict) -> dict:
    """
    VALIDATED against real Weatherford drawing title block structure:
    Part Number / Model File / Model Version / Drawing File / Drawing Version.

    In the PoC, title_block is passed in manually (or via a simple form) since OCR/PDF
    title-block parsing is a further-out refinement, not needed to validate the pipeline shape.
    Expected keys: part_number, model_file, model_version, drawing_file, drawing_version.
    """
    required = ["part_number", "model_file", "model_version", "drawing_file", "drawing_version"]
    missing = [k for k in required if k not in title_block]
    if missing:
        raise ValueError(f"MBD title block missing expected fields: {missing}")

    return {
        "part_no": title_block["part_number"],
        "revision": title_block["drawing_version"],
        "model_file": title_block["model_file"],
        "model_version": title_block["model_version"],
    }


def extract_sop_metadata_placeholder(filename: str) -> dict:
    """
    PLACEHOLDER — no real Weatherford SOP sample received yet.
    Falls back to filename parsing only. Revisit once real SOP (ideally animated) sample arrives.
    """
    meta = extract_from_filename(filename)
    meta["_status"] = "PLACEHOLDER — validate against real SOP sample when available"
    return meta


def extract_nc_metadata_placeholder(filename: str) -> dict:
    """
    PLACEHOLDER — no real Weatherford NC program sample received yet.
    Falls back to filename parsing only. Revisit once real NC sample arrives.
    """
    meta = extract_from_filename(filename)
    meta["_status"] = "PLACEHOLDER — validate against real NC program sample when available"
    return meta
