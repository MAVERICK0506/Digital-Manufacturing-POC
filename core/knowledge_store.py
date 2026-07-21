"""
Knowledge Store — Step 4. Holds METADATA, RELATIONSHIPS, and FILE REFERENCES only.
It never owns the actual engineering files — those live via the Storage Adapter
(local disk in PoC, Windchill vault in production). See architecture doc D.1.

The 4 "bins" (MBD Store / MBOM Store / NC Programs / SOPs-Anims) from the official
spec are NOT 4 separate tables — they are the doc_type column on the single
Documents table, filtered. See architecture doc D.2.
"""

import sqlite3
import os


def get_connection(db_path: str) -> sqlite3.Connection:
    # check_same_thread=False: needed because Streamlit can call into this connection
    # from different threads across interactions. Safe here because @st.cache_resource
    # in the app ensures only one shared connection object is ever created.
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection, schema_path: str):
    with open(schema_path, "r") as f:
        conn.executescript(f.read())
    conn.commit()


def upsert_part(conn: sqlite3.Connection, part_no: str, description: str = None,
                 supplier: str = None, assembly_part_no: str = None) -> int:
    """Insert a part if it doesn't exist; return its part_id either way."""
    cur = conn.execute("SELECT part_id FROM Parts WHERE part_no = ?", (part_no,))
    row = cur.fetchone()
    if row:
        return row[0]

    assembly_id = None
    if assembly_part_no:
        cur = conn.execute("SELECT part_id FROM Parts WHERE part_no = ?", (assembly_part_no,))
        r = cur.fetchone()
        assembly_id = r[0] if r else None

    cur = conn.execute(
        "INSERT INTO Parts (part_no, description, supplier, assembly_id) VALUES (?, ?, ?, ?)",
        (part_no, description, supplier, assembly_id),
    )
    conn.commit()
    return cur.lastrowid


def insert_document(conn: sqlite3.Connection, part_no: str, doc_type: str,
                     source_ref: str, revision: str = None) -> int:
    """
    Inserts a new Documents row. If an ACTIVE document of the same part_no + doc_type
    already exists, it is marked 'superseded' first — this is the append-only version
    control rule that solves the Rev A/B ambiguity problem.
    """
    part_id = upsert_part(conn, part_no)

    conn.execute(
        """UPDATE Documents SET status = 'superseded'
           WHERE part_id = ? AND doc_type = ? AND status = 'active'""",
        (part_id, doc_type.upper()),
    )

    cur = conn.execute(
        """INSERT INTO Documents (part_id, doc_type, source_ref, revision, status)
           VALUES (?, ?, ?, ?, 'active')""",
        (part_id, doc_type.upper(), source_ref, revision),
    )
    conn.commit()
    return cur.lastrowid


def insert_relationship(conn: sqlite3.Connection, parent_part_no: str, child_part_no: str,
                         bom_level: int = 1, qty: float = 1.0):
    parent_id = upsert_part(conn, parent_part_no)
    child_id = upsert_part(conn, child_part_no)
    conn.execute(
        """INSERT OR REPLACE INTO Relationships (parent_part_id, child_part_id, bom_level, qty)
           VALUES (?, ?, ?, ?)""",
        (parent_id, child_id, bom_level, qty),
    )
    conn.commit()


def get_active_document(conn: sqlite3.Connection, part_no: str, doc_type: str) -> dict:
    cur = conn.execute(
        """SELECT d.doc_id, d.source_ref, d.revision, d.date_received, d.status
           FROM Documents d JOIN Parts p ON d.part_id = p.part_id
           WHERE p.part_no = ? AND d.doc_type = ? AND d.status = 'active'""",
        (part_no, doc_type.upper()),
    )
    row = cur.fetchone()
    if not row:
        return None
    cols = ["doc_id", "source_ref", "revision", "date_received", "status"]
    return dict(zip(cols, row))


def get_all_documents_for_part(conn: sqlite3.Connection, part_no: str) -> list:
    """The 'show me everything for this part' cross-reference query — the whole point
    of a single Documents table instead of 4 separate bins."""
    cur = conn.execute(
        """SELECT d.doc_type, d.source_ref, d.revision, d.status
           FROM Documents d JOIN Parts p ON d.part_id = p.part_id
           WHERE p.part_no = ? ORDER BY d.doc_type""",
        (part_no,),
    )
    cols = ["doc_type", "source_ref", "revision", "status"]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_revision_history(conn: sqlite3.Connection, part_no: str, doc_type: str) -> list:
    cur = conn.execute(
        """SELECT d.doc_id, d.revision, d.status, d.date_received
           FROM Documents d JOIN Parts p ON d.part_id = p.part_id
           WHERE p.part_no = ? AND d.doc_type = ? ORDER BY d.date_received""",
        (part_no, doc_type.upper()),
    )
    cols = ["doc_id", "revision", "status", "date_received"]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
