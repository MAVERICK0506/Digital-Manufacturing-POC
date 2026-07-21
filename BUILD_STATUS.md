# Build Status — Digital Thread POC

## ✅ Fully built and tested (end-to-end smoke test passes)

| Component | File | Status |
|---|---|---|
| DB schema (Parts/Documents/Relationships/Versions/AuditLog/Users) | `db/schema.sql` | Done |
| Data Source Adapter interface + Local implementation | `adapters/` | Done |
| Windchill adapter | `adapters/windchill_adapter_stub.py` | **Documented stub, deliberately not implemented** — blocked on IT/PLM admin input (API variant, auth, licensing) |
| Storage Adapter (local FS) | `core/storage_adapter.py` | Done |
| IP Validation Gate (type whitelist, scope check, integrity check) | `core/ip_gate.py` | Done — deep IP-content inspection explicitly out of scope, flagged |
| Knowledge Store (single Documents table, doc_type-filtered "bins", append-only versioning) | `core/knowledge_store.py` | Done, tested — Rev A/B supersession confirmed working |
| Ingest Engine (orchestrates gate → extract → store → DB → audit) | `core/ingest_engine.py` | Done |
| Audit Log (append-only) | `core/audit.py` | Done |
| Access Control (single permission map, role-gated retrieval) | `core/access_control.py` | Done, tested — ShopFloor correctly denied MBOM, allowed SOP |
| Query Engine (structured search + cross-reference) | `core/query_engine.py` | Done |
| Intent Resolver (free text → structured filter) | `llm/intent_resolver.py` | Rule-based fallback done and tested; **real LLM API call not wired up yet** (stubbed, ready to swap in) |
| Streamlit UI (Upload / Search / Audit tabs) | `app/streamlit_app.py` | Built, imports verified — not yet demoed live |
| End-to-end test | `tests/test_end_to_end.py` | Passing — ingest all 4 types, structured query, role denial, cross-reference, revision history, audit trail all confirmed working |

## ⚠️ Metadata extraction — validated vs. placeholder (by design, see chat discussion)

| Doc type | Extraction logic | Status |
|---|---|---|
| MBD | Title-block fields (Part Number/Model File/Model Version/Drawing File/Drawing Version) | **Validated** against real Weatherford drawing field structure (from Lokesh's shared image) |
| MBOM | Column parser (Number/Name/Quantity/UOM etc.) | **Validated** against real Weatherford BOM PDF structure (part 02736321, 27-line BOM) |
| SOP | Filename-pattern only | **Placeholder** — no real Weatherford SOP sample received. Revisit when sample arrives. |
| NC | Filename-pattern only | **Placeholder** — no real Weatherford NC program sample received. Revisit when sample arrives. |

## Sample data — anchored to ONE real part (deliberate decision, see chat)

All synthetic sample files reference the **same real part family** from Weatherford's actual BOM (assembly `02736321`, component `00158794`), so cross-referencing demos meaningfully instead of linking unrelated files:
- `00158794_MBD_RevB.6.pdf` — real title-block fields, file itself is a placeholder (native Creo/STEP model not received)
- `02736321_MBOM_RevD.xlsx` — real BOM line items transcribed from actual Weatherford PDF
- `02736321_SOP_RevA.pdf` — fully synthetic, step names derived from the real assembly tree structure
- `00158794_NC_Rev1.nc` — generic G-code structure, relabeled with the real part number

## ❌ Not built / explicitly out of scope for this POC

- Real Windchill API integration (blocked on IT/PLM admin — auth model, API variant, licensing all unconfirmed)
- Deep IP-content inspection inside the validation gate (needs CAD-format-specific tooling)
- Real authentication/SSO (role is manually selected in the demo UI, not tied to a real login system)
- Real LLM API call in intent_resolver (rule-based fallback works and is tested; swapping in a real API call is a small, isolated change when ready)
- PDF/OCR-based automatic title-block extraction for MBD (currently the title block is passed in manually/via form — automating this is a further-out refinement, not needed to validate the pipeline shape)

## Next steps, in order
1. Demo the Streamlit app live (`streamlit run app/streamlit_app.py`) to confirm the UI matches the tested backend behavior.
2. Get real SOP and NC program samples → refine `metadata_provider.py`'s two placeholder functions.
3. Wire up a real LLM call in `intent_resolver._call_llm()` (isolated, small change).
4. Take the Windchill API question (variant/auth/licensing) to IT/PLM admin — only then attempt `windchill_adapter_stub.py`.
