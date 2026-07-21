"""
DataSourceAdapter — interface contract for "where do supplier files come from".

PoC implementation: LocalAdapter (reads a local /inbox folder).
Production implementation: WindchillAdapter (calls Windchill REST API) — STUB ONLY,
kept undone deliberately because the real API variant/auth/licensing at Weatherford
is unconfirmed (open dependency, see architecture doc Part D.1).

Nothing outside this file and its implementations should know or care which one is active.
"""

from abc import ABC, abstractmethod
from typing import List, Dict


class DataSourceAdapter(ABC):

    @abstractmethod
    def list_documents(self) -> List[Dict]:
        """Return a list of available document descriptors waiting to be ingested.
        Each descriptor: {"filename": str, "local_path": str}
        (In the Windchill implementation, local_path would instead be a Windchill doc ID.)
        """
        raise NotImplementedError

    @abstractmethod
    def get_document(self, ref: str) -> bytes:
        """Return the raw bytes of a document given its reference (path or Windchill ID)."""
        raise NotImplementedError

    @abstractmethod
    def submit_document(self, local_path: str) -> str:
        """Register/submit a new document into the source. Returns a reference string."""
        raise NotImplementedError
