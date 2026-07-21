# How to Run This Locally

## 1. Requirements
- Python 3.9+ installed on your machine
- Terminal/command prompt access

Check your Python version:
```
python3 --version
```

## 2. Unzip and enter the project
```
unzip digital_thread_poc.zip
cd digital_thread_poc
```

## 3. Install dependencies
```
pip install -r requirements.txt
```
(If you're on a system that blocks global installs, use: `pip install -r requirements.txt --break-system-packages`
or create a virtual environment first: `python3 -m venv venv && source venv/bin/activate` — Windows: `venv\Scripts\activate`)

## 4. Run the automated test first (proves the whole pipeline works)
```
python3 tests/test_end_to_end.py
```
You should see output for: ingesting all 4 sample files, structured queries (including a role
being correctly denied), a cross-reference query, revision history showing supersession, and
the audit trail. This creates `db/digital_thread_test.db` and a `storage_test/` folder — both
safe to delete and regenerate any time by re-running the script.

## 5. Run the interactive demo (Streamlit UI)
```
streamlit run app/streamlit_app.py
```
This opens in your browser automatically (usually `http://localhost:8501`). If it doesn't,
copy the URL shown in the terminal.

**Try this in the UI:**
- **Upload tab** — upload one of the files from `sample_data/` (pick the matching Document
  Type from the dropdown, and enter the part number, e.g. `02736321` or `00158794`). Try
  uploading a wrong file type for a doc type (e.g. a `.jpg` as MBOM) to see the IP gate reject it.
- **Search tab** — switch role between Engineer / ShopFloor / QA and search for the same
  document to see access control in action (e.g. ShopFloor should be denied MBOM but
  allowed SOP/NC). Try "Free text (NL)" mode with something like
  *"show me the SOP for 02736321"*.
- **Audit Log tab** — see every action logged, including rejections and denials.

This app runs entirely on your machine — nothing goes to the cloud, no API key needed
(the NL query mode uses the built-in rule-based fallback, not a live LLM call).

## 6. Resetting the demo
To start fresh (wipe all ingested data):
```
rm -f db/digital_thread.db
rm -rf storage
```
Then re-run step 5 — the app will recreate the database automatically on first load.

## 7. Regenerating sample data
If you ever edit `sample_data/generate_samples.py`, re-run it with:
```
python3 sample_data/generate_samples.py
```

## Where to look for what's built vs. still placeholder
See `BUILD_STATUS.md` in this same folder — it tracks exactly which pieces are validated
against real Weatherford file formats, and which are intentional placeholders pending real
samples or IT/PLM admin input (e.g. Windchill API access).
