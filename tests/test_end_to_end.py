"""
End-to-end smoke test: ingest all 4 sample files, then run structured queries
including the cross-reference and role-denial cases.

Run: python3 tests/test_end_to_end.py   (from project root)
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import knowledge_store, ingest_engine, query_engine, audit
from core.storage_adapter import LocalStorageAdapter

DB_PATH = "db/digital_thread_test.db"
SCHEMA_PATH = "db/schema.sql"
STORAGE_DIR = "storage_test"


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = knowledge_store.get_connection(DB_PATH)
    knowledge_store.init_db(conn, SCHEMA_PATH)
    storage = LocalStorageAdapter(STORAGE_DIR)

    print("=" * 70)
    print("STEP 1-4: INGEST")
    print("=" * 70)

    # MBD (title block passed explicitly, since real title-block OCR is a further-out step)
    title_block = {
        "part_number": "00158794", "model_file": "00158794", "model_version": "B.6",
        "drawing_file": "00158794", "drawing_version": "B.6",
    }
    r1 = ingest_engine.ingest_file(conn, storage, "sample_data/00158794_MBD_RevB.6.pdf",
                                     "MBD", user_id="ayush", title_block=title_block)
    print("MBD ingest:", r1)

    r2 = ingest_engine.ingest_file(conn, storage, "sample_data/02736321_MBOM_RevD.xlsx",
                                     "MBOM", user_id="ayush")
    print("MBOM ingest:", r2)
    n_lines = ingest_engine.ingest_mbom_lines(conn, "sample_data/02736321_MBOM_RevD.xlsx",
                                                assembly_part_no="02736321")
    print(f"MBOM relationship lines ingested: {n_lines}")

    r3 = ingest_engine.ingest_file(conn, storage, "sample_data/02736321_SOP_RevA.pdf",
                                     "SOP", user_id="ayush")
    print("SOP ingest (placeholder):", r3)

    r4 = ingest_engine.ingest_file(conn, storage, "sample_data/00158794_NC_Rev1.nc",
                                     "NC", user_id="ayush")
    print("NC ingest (placeholder):", r4)

    print()
    print("=" * 70)
    print("STEP 5-6: QUERY (structured, with role enforcement)")
    print("=" * 70)

    # Engineer asking for MBOM on the assembly -> should succeed
    res = query_engine.run_structured_query(conn, storage, "02736321", "MBOM",
                                              user_id="ayush", role="Engineer")
    print("Engineer -> MBOM query:", {"found": res["found"], "denied": res["denied"]})

    # ShopFloor asking for MBOM -> should be denied (ShopFloor only sees SOP/NC)
    res2 = query_engine.run_structured_query(conn, storage, "02736321", "MBOM",
                                               user_id="rahul", role="ShopFloor")
    print("ShopFloor -> MBOM query:", {"found": res2["found"], "denied": res2["denied"]})

    # ShopFloor asking for SOP -> should succeed
    res3 = query_engine.run_structured_query(conn, storage, "02736321", "SOP",
                                               user_id="rahul", role="ShopFloor")
    print("ShopFloor -> SOP query:", {"found": res3["found"], "denied": res3["denied"]})

    # Cross-reference: everything for part 00158794, as QA (sees all types)
    cross = query_engine.cross_reference_part(conn, "00158794", user_id="qa_user", role="QA")
    print("QA cross-reference for part 00158794:", cross)

    print()
    print("=" * 70)
    print("REVISION HISTORY CHECK (append-only versioning)")
    print("=" * 70)
    # Ingest a second MBD revision for the same part, confirm old one gets superseded
    title_block_v2 = dict(title_block, drawing_version="B.7")
    with open("sample_data/00158794_MBD_RevB.7.pdf", "w") as f:
        f.write("Simulated Rev B.7 of same part\n")
    ingest_engine.ingest_file(conn, storage, "sample_data/00158794_MBD_RevB.7.pdf",
                                "MBD", user_id="ayush", title_block=title_block_v2)
    history = knowledge_store.get_revision_history(conn, "00158794", "MBD")
    print("MBD revision history for 00158794:", history)

    print()
    print("=" * 70)
    print("AUDIT TRAIL (last 5 entries)")
    print("=" * 70)
    trail = audit.get_audit_trail(conn)
    for entry in trail[:5]:
        print(" ", entry)

    conn.close()
    print()
    print("ALL CHECKS COMPLETE.")


if __name__ == "__main__":
    main()
