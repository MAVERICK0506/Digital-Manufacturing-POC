"""
StorageAdapter — interface for "where do validated files get physically stored/retrieved from".

PoC: LocalStorageAdapter, saves into storage/{doc_type}/.
Production: would point to Windchill's Document Vault instead — same interface,
no change needed in knowledge_store.py or query_engine.py when swapped.
"""

import os
import shutil
from abc import ABC, abstractmethod


class StorageAdapter(ABC):

    @abstractmethod
    def save(self, doc_type: str, filename: str, src_path: str) -> str:
        """Store a file, return the source_ref to save in the Documents table."""
        raise NotImplementedError

    @abstractmethod
    def retrieve(self, source_ref: str) -> bytes:
        """Fetch raw file bytes given a source_ref."""
        raise NotImplementedError


class LocalStorageAdapter(StorageAdapter):

    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def save(self, doc_type: str, filename: str, src_path: str) -> str:
        target_dir = os.path.join(self.base_dir, doc_type.lower())
        os.makedirs(target_dir, exist_ok=True)
        dest = os.path.join(target_dir, filename)
        if os.path.abspath(src_path) != os.path.abspath(dest):
            shutil.copy(src_path, dest)
        return dest  # this becomes the Documents.source_ref

    def retrieve(self, source_ref: str) -> bytes:
        with open(source_ref, "rb") as f:
            return f.read()
