"""
Digital Thread POC — Streamlit demo UI.
Run from project root: streamlit run app/streamlit_app.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from core import knowledge_store, ingest_engine, query_engine, access_control, audit
from core.storage_adapter import LocalStorageAdapter
from llm import intent_resolver

DB_PATH = "db/digital_thread.db"
SCHEMA_PATH = "db/schema.sql"
STORAGE_DIR = "storage"

st.set_page_config(page_title="Digital Thread POC", layout="wide")


@st.cache_resource
def get_conn():
    is_new = not os.path.exists(DB_PATH)
    conn = knowledge_store.get_connection(DB_PATH)
    if is_new:
        knowledge_store.init_db(conn, SCHEMA_PATH)
    return conn


conn = get_conn()
storage = LocalStorageAdapter(STORAGE_DIR)

st.title("Digital Manufacturing POC — Digital Thread Prototype")
st.caption("Hydrow II-AP Packer · Intelligent Manufacturing Data Agent")

tab_upload, tab_search, tab_audit = st.tabs(["📤 Upload (Supplier Submission)", "🔎 Search", "🧾 Audit Log"])

# ---------------- UPLOAD TAB ----------------
with tab_upload:
    st.subheader("Step 1-4: Supplier Submission → IP Gate → Ingest → Knowledge Store")
    uploaded = st.file_uploader("Drop a supplier file", type=None)
    doc_type = st.selectbox("Document type", ["MBD", "MBOM", "NC", "SOP"])
    part_no_hint = st.text_input("Part number (required for MBD/NC/SOP; MBOM parses its own)")

    if uploaded and st.button("Submit through pipeline"):
        tmp_path = os.path.join("inbox", uploaded.name)
        os.makedirs("inbox", exist_ok=True)
        with open(tmp_path, "wb") as f:
            f.write(uploaded.getbuffer())

        title_block = None
        if doc_type == "MBD" and part_no_hint:
            title_block = {
                "part_number": part_no_hint, "model_file": part_no_hint,
                "model_version": "manual", "drawing_file": part_no_hint, "drawing_version": "manual",
            }

        result = ingest_engine.ingest_file(conn, storage, tmp_path, doc_type,
                                            user_id="streamlit_user", title_block=title_block,
                                            part_no_override=part_no_hint if part_no_hint else None)

        if result["status"] == "ingested":
            st.success(f"Ingested — doc_id={result['doc_id']}, part_no={result['part_no']}")
            if doc_type == "MBOM" and part_no_hint:
                n = ingest_engine.ingest_mbom_lines(conn, tmp_path, assembly_part_no=part_no_hint)
                st.info(f"Parsed {n} BOM lines into Relationships table")
        else:
            st.error(f"REJECTED — {result['reason_code']}: {result.get('detail')}")

# ---------------- SEARCH TAB ----------------
with tab_search:
    st.subheader("Step 5-6: Query + Intent Resolution + Role-Based Output")

    col1, col2 = st.columns(2)
    with col1:
        role = st.selectbox("Acting as role", ["Engineer", "ShopFloor", "QA", "Admin"])
        user_id = st.text_input("User ID", value="demo_user")
    with col2:
        mode = st.radio("Query mode", ["Structured", "Free text (NL)"])

    if mode == "Structured":
        c1, c2 = st.columns(2)
        part_no = c1.text_input("Part number", value="02736321")
        doc_type_q = c2.selectbox("Document type", ["MBD", "MBOM", "NC", "SOP"], key="query_doctype")

        if st.button("Search"):
            res = query_engine.run_structured_query(conn, storage, part_no, doc_type_q, user_id, role)
            if res["denied"]:
                st.warning(f"Document exists, but role '{role}' does not have access to {doc_type_q}.")
            elif res["found"]:
                st.success(f"Found — revision {res['meta']['revision']}, status {res['meta']['status']}")
                st.download_button("Download", res["content"], file_name=os.path.basename(res['meta']['source_ref']))
            else:
                st.info("No active document found for that part/type.")

        st.divider()
        st.caption("Cross-reference: show everything for a part")
        if st.button("Show all documents for this part"):
            results = query_engine.cross_reference_part(conn, part_no, user_id, role)
            if results:
                st.table(results)
            else:
                st.info("No documents found (or none visible to this role).")

    else:
        free_text = st.text_input("Ask in plain English", value="show me the latest SOP for 02736321")
        if st.button("Ask"):
            intent = intent_resolver.resolve_intent(free_text, use_llm=False)
            st.json(intent)
            if intent["doc_type"] and intent["part_no"]:
                res = query_engine.run_structured_query(
                    conn, storage, intent["part_no"], intent["doc_type"], user_id, role
                )
                if res["denied"]:
                    st.warning(f"Document exists, but role '{role}' does not have access.")
                elif res["found"]:
                    st.success(f"Found — revision {res['meta']['revision']}")
                    st.download_button("Download", res["content"],
                                        file_name=os.path.basename(res['meta']['source_ref']))
                else:
                    st.info("No matching document found.")
            else:
                st.error("Could not resolve doc_type/part_no from that query — try being more specific.")

# ---------------- AUDIT TAB ----------------
with tab_audit:
    st.subheader("Step 7: Version Control + Audit Trail")
    trail = audit.get_audit_trail(conn)
    if trail:
        st.dataframe(trail, use_container_width=True)
    else:
        st.info("No activity logged yet.")
