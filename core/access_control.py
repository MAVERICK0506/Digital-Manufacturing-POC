"""
Access Control — Step 6. One permission map, checked once per request,
not four duplicate engines. See chat discussion on this exact question.
"""

ROLE_PERMISSIONS = {
    "Engineer":  {"MBD", "MBOM"},
    "ShopFloor": {"SOP", "NC"},
    "QA":        {"MBD", "MBOM", "NC", "SOP"},   # + full audit history, handled separately
    "Admin":     {"MBD", "MBOM", "NC", "SOP"},   # + rejected files/reason codes
}


class AccessDeniedError(Exception):
    pass


def is_allowed(role: str, doc_type: str) -> bool:
    return doc_type.upper() in ROLE_PERMISSIONS.get(role, set())


def enforce(role: str, doc_type: str):
    """Raises AccessDeniedError if the role can't see this doc_type. Call before returning any file."""
    if not is_allowed(role, doc_type):
        raise AccessDeniedError(
            f"Role '{role}' is not permitted to access doc_type '{doc_type}'"
        )
