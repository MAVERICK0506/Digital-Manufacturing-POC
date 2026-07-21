"""
Structured Ingest Engine — Step 3. Orchestrates: IP Gate -> Metadata extraction ->
Storage Adapter -> Knowledge Store insert -> Audit log. This is the module that ties
every other core/ piece together into the actual per-file pipeline.
"""

import os
import sqlite3

from core import ip_gate, metadata_provider, knowledge_store, audit
from core.storage_adapter import StorageAdapter


def ingest_file(conn: sqlite3.Connection, storage: StorageAdapter, filepath: str,
                 declared_doc_type: str, user_id: str = "system",
                 title_block: dict = None, part_no_override: str = None) -> dict:
    """
    Runs one file through the full pipeline. Returns a result dict:
    {"status": "ingested"|"rejected", "doc_id": int|None, "reason_code": str|None}

    part_no_override: if provided (e.g. typed into the UI form), this takes priority
    over filename-based extraction — needed because real supplier filenames rarely
    follow a clean PARTNO_DOCTYPE_RevX convention.
    """
    filename = os.path.basename(filepath)
    declared_doc_type = declared_doc_type.upper()

    # --- Step 3a: pre-extraction (needed to know part_no for scope check in IP gate) ---
    part_no = None
    revision = None
    extra_meta = {}

    if declared_doc_type == "MBD":
        if title_block:
            meta = metadata_provider.extract_mbd_metadata(title_block)
            part_no, revision = meta["part_no"], meta["revision"]
            extra_meta = meta
        else:
            fn_meta = metadata_provider.extract_from_filename(filename)
            part_no, revision = fn_meta["part_no"], fn_meta["revision"]

    elif declared_doc_type == "MBOM":
        fn_meta = metadata_provider.extract_from_filename(filename)
        part_no, revision = fn_meta["part_no"], fn_meta["revision"]
        # Full line-item extraction happens separately via ingest_mbom_lines() below,
        # since an MBOM file describes MANY parts, not just one.

    elif declared_doc_type == "SOP":
        meta = metadata_provider.extract_sop_metadata_placeholder(filename)
        part_no, revision = meta["part_no"], meta["revision"]
        extra_meta = meta

    elif declared_doc_type == "NC":
        meta = metadata_provider.extract_nc_metadata_placeholder(filename)
        part_no, revision = meta["part_no"], meta["revision"]
        extra_meta = meta

    # Explicit override (e.g. typed into the UI) always wins over filename parsing —
    # real supplier filenames rarely follow a clean PARTNO_DOCTYPE_RevX convention.
    if part_no_override:
        part_no = part_no_override
    if not revision:
        revision = "unspecified"

    # --- Step 2: IP Validation Gate ---
    result = ip_gate.validate(filepath, declared_doc_type, declared_part_no=part_no)

    if not result.passed:
        audit.log_action(conn, user_id, "reject", filename,
                          f"{result.reason_code}: {result.detail}")
        return {"status": "rejected", "doc_id": None, "reason_code": result.reason_code,
                "detail": result.detail}

    audit.log_action(conn, user_id, "submit", filename, "passed IP gate")

    # --- Step 3b: Storage ---
    source_ref = storage.save(declared_doc_type, filename, filepath)

    # --- Step 4: Knowledge Store insert ---
    if not part_no:
        part_no = f"UNKNOWN_{filename}"  # never silently drop — flag it instead of failing

    doc_id = knowledge_store.insert_document(conn, part_no, declared_doc_type, source_ref, revision)

    audit.log_action(conn, user_id, "ingest", doc_id, f"doc_type={declared_doc_type}, part_no={part_no}")

    return {"status": "ingested", "doc_id": doc_id, "reason_code": None, "part_no": part_no,
            "extra_meta": extra_meta}


def ingest_mbom_lines(conn: sqlite3.Connection, mbom_filepath: str, assembly_part_no: str):
    """
    Special-cased: an MBOM/eBOM file lists MANY child parts under one assembly.
    Parses the real Weatherford BOM structure and populates Parts + Relationships.
    """
    lines = metadata_provider.extract_mbom_metadata(mbom_filepath)
    for line in lines:
        knowledge_store.insert_relationship(
            conn, parent_part_no=assembly_part_no, child_part_no=line["part_no"],
            bom_level=1, qty=line["qty"],
        )
    return len(lines)
