"""
Query Engine — Step 5. Structured filters always resolved via SQL (deterministic).
The LLM (llm/intent_resolver.py) only ever translates free text INTO a structured
filter before it reaches this module — it never generates the answer itself.
"""

import sqlite3

from core import knowledge_store, access_control, audit
from core.storage_adapter import StorageAdapter


def run_structured_query(conn: sqlite3.Connection, storage: StorageAdapter,
                          part_no: str, doc_type: str, user_id: str, role: str) -> dict:
    """
    The single retrieval path everyone uses (Engineer/ShopFloor/QA/Admin alike).
    Returns {"found": bool, "content": bytes|None, "meta": dict|None, "denied": bool}
    """
    doc = knowledge_store.get_active_document(conn, part_no, doc_type)

    if not doc:
        audit.log_action(conn, user_id, "query", f"{part_no}/{doc_type}", "not_found")
        return {"found": False, "content": None, "meta": None, "denied": False}

    audit.log_action(conn, user_id, "query", doc["doc_id"], "found")

    # --- Step 6 enforcement point: check BEFORE returning any file content ---
    if not access_control.is_allowed(role, doc_type):
        audit.log_action(conn, user_id, "retrieve", doc["doc_id"], f"DENIED (role={role})")
        return {"found": True, "content": None, "meta": doc, "denied": True}

    content = storage.retrieve(doc["source_ref"])
    audit.log_action(conn, user_id, "retrieve", doc["doc_id"], f"ALLOWED (role={role})")

    return {"found": True, "content": content, "meta": doc, "denied": False}


def cross_reference_part(conn: sqlite3.Connection, part_no: str, user_id: str, role: str) -> list:
    """'Show me everything for this part' — the query the single-table design exists for."""
    all_docs = knowledge_store.get_all_documents_for_part(conn, part_no)
    audit.log_action(conn, user_id, "query", part_no, f"cross_reference: {len(all_docs)} docs found")
    # Filter to only what this role is allowed to see
    return [d for d in all_docs if access_control.is_allowed(role, d["doc_type"])]
