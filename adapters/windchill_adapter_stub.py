"""
WindchillAdapter — PRODUCTION STUB, NOT IMPLEMENTED.

This exists to prove the DataSourceAdapter interface holds for the real integration.
It is intentionally left unimplemented because three things are unconfirmed for
Weatherford's specific Windchill 12.1.2.0 instance:

  1. Which REST API variant is enabled (WRS / OSLC / ThingWorx-based — version-dependent)
  2. The authentication model (API key / OAuth / service account / SSO-integrated)
  3. Whether API-level document retrieval is itself separately licensed

These require a conversation with Weatherford's IT/PLM admin before this can become
real code. Until then, LocalAdapter is the active implementation everywhere in this system.

When ready, implement each method below to call the real Windchill REST endpoints,
and swap the adapter in app config — no other module in this codebase needs to change.
"""

from typing import List, Dict
from adapters.data_source_adapter import DataSourceAdapter


class WindchillAdapter(DataSourceAdapter):

    def __init__(self, api_url: str, auth_token: str):
        self.api_url = api_url
        self.auth_token = auth_token
        raise NotImplementedError(
            "WindchillAdapter is a documented stub. Real implementation pending "
            "Weatherford IT/PLM admin input on API access, auth, and licensing."
        )

    def list_documents(self) -> List[Dict]:
        raise NotImplementedError

    def get_document(self, ref: str) -> bytes:
        raise NotImplementedError

    def submit_document(self, local_path: str) -> str:
        raise NotImplementedError
