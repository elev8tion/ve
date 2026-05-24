from __future__ import annotations

import json
from typing import Any, Dict, Optional

import keyring

from .constants import CODEX_STORAGE_SERVICE, CODEX_STORAGE_USERNAME


def save_tokens(tokens: Dict[str, Any]) -> None:
    """Save tokens securely using keyring."""
    keyring.set_password(
        CODEX_STORAGE_SERVICE,
        CODEX_STORAGE_USERNAME,
        json.dumps(tokens),
    )


def load_tokens() -> Optional[Dict[str, Any]]:
    """Load tokens from keyring."""
    data = keyring.get_password(CODEX_STORAGE_SERVICE, CODEX_STORAGE_USERNAME)
    if not data:
        return None
    try:
        return json.loads(data)
    except Exception:
        return None


def delete_tokens() -> None:
    """Delete stored tokens."""
    try:
        keyring.delete_password(CODEX_STORAGE_SERVICE, CODEX_STORAGE_USERNAME)
    except Exception:
        pass


def has_valid_tokens() -> bool:
    """Check if valid tokens exist."""
    return load_tokens() is not None