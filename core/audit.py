"""
Audit — Step 7. Append-only log of every submit/reject/ingest/query/retrieve action.
Never UPDATE or DELETE against AuditLog — only INSERT.
"""

import sqlite3


def log_action(conn: sqlite3.Connection, user_id: str, action_type: str, target_id: str, result: str):
    assert action_type in ("submit", "reject", "ingest", "query", "retrieve"), \
        f"Invalid action_type: {action_type}"
    conn.execute(
        "INSERT INTO AuditLog (user_id, action_type, target_id, result) VALUES (?, ?, ?, ?)",
        (user_id, action_type, str(target_id), result),
    )
    conn.commit()


def get_audit_trail(conn: sqlite3.Connection, target_id: str = None) -> list:
    """Retrieve audit history, optionally filtered to one target (e.g. one doc_id)."""
    if target_id:
        cur = conn.execute(
            "SELECT * FROM AuditLog WHERE target_id = ? ORDER BY timestamp DESC", (str(target_id),)
        )
    else:
        cur = conn.execute("SELECT * FROM AuditLog ORDER BY timestamp DESC")
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]
