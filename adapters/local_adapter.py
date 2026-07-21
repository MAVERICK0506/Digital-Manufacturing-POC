"""LocalAdapter — PoC implementation of DataSourceAdapter, reads from a local /inbox folder."""

import os
import shutil
from typing import List, Dict

from adapters.data_source_adapter import DataSourceAdapter


class LocalAdapter(DataSourceAdapter):

    def __init__(self, inbox_path: str):
        self.inbox_path = inbox_path
        os.makedirs(self.inbox_path, exist_ok=True)

    def list_documents(self) -> List[Dict]:
        docs = []
        for fname in sorted(os.listdir(self.inbox_path)):
            full_path = os.path.join(self.inbox_path, fname)
            if os.path.isfile(full_path):
                docs.append({"filename": fname, "local_path": full_path})
        return docs

    def get_document(self, ref: str) -> bytes:
        with open(ref, "rb") as f:
            return f.read()

    def submit_document(self, local_path: str) -> str:
        """Simulates a supplier dropping a file into the inbox (copies it in if not already there)."""
        fname = os.path.basename(local_path)
        dest = os.path.join(self.inbox_path, fname)
        if os.path.abspath(local_path) != os.path.abspath(dest):
            shutil.copy(local_path, dest)
        return dest
