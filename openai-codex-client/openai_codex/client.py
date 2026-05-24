from __future__ import annotations

import time
from typing import Any, Dict, Optional

import httpx

from .constants import (
    CODEX_ACCESS_TOKEN_REFRESH_SKEW_SECONDS,
    CODEX_OAUTH_CLIENT_ID,
    CODEX_OAUTH_ISSUER,
    CODEX_OAUTH_TOKEN_URL,
)
from .storage import delete_tokens, load_tokens, save_tokens


class OpenAICodexOAuthClient:
    """Standalone OpenAI Codex (ChatGPT) OAuth client.

    Handles device-code login, token storage, and automatic refresh.
    """

    def __init__(self):
        self._tokens: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def login(self) -> None:
        """Perform device code login flow."""
        tokens = self._device_code_login()
        save_tokens(tokens)
        self._tokens = tokens
        print("\n✅ Login successful! Tokens saved securely.")

    def logout(self) -> None:
        """Remove stored tokens."""
        delete_tokens()
        self._tokens = None
        print("Logged out and tokens removed.")

    def status(self) -> Dict[str, Any]:
        """Return current auth status."""
        tokens = self._get_valid_tokens()
        if not tokens:
            return {"authenticated": False}
        return {
            "authenticated": True,
            "has_refresh_token": bool(tokens.get("refresh_token")),
        }

    def get_access_token(self) -> str:
        """Return a valid access token (refreshes if needed)."""
        tokens = self._get_valid_tokens()
        if not tokens:
            raise RuntimeError("Not authenticated. Run `openai-codex login` first.")
        return tokens["access_token"]

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _get_valid_tokens(self) -> Optional[Dict[str, Any]]:
        if self._tokens:
            if self._needs_refresh(self._tokens):
                self._tokens = self._refresh(self._tokens)
            return self._tokens

        tokens = load_tokens()
        if not tokens:
            return None

        if self._needs_refresh(tokens):
            tokens = self._refresh(tokens)
            if tokens:
                save_tokens(tokens)

        self._tokens = tokens
        return tokens

    def _needs_refresh(self, tokens: Dict[str, Any]) -> bool:
        expires_at = tokens.get("expires_at")
        if not expires_at:
            return True
        return time.time() > (expires_at - CODEX_ACCESS_TOKEN_REFRESH_SKEW_SECONDS)

    def _refresh(self, tokens: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            return None

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    CODEX_OAUTH_TOKEN_URL,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": CODEX_OAUTH_CLIENT_ID,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                if resp.status_code != 200:
                    return None
                new_tokens = resp.json()
                # Preserve refresh_token if not returned
                if "refresh_token" not in new_tokens:
                    new_tokens["refresh_token"] = refresh_token
                new_tokens["expires_at"] = time.time() + new_tokens.get("expires_in", 3600)
                return new_tokens
        except Exception:
            return None

    def _device_code_login(self) -> Dict[str, Any]:
        """Run the full device code flow for openai-codex."""
        import time as _time

        client_id = CODEX_OAUTH_CLIENT_ID
        issuer = CODEX_OAUTH_ISSUER

        # Step 1: Request device code
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                f"{issuer}/api/accounts/deviceauth/usercode",
                json={"client_id": client_id},
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Device code request failed: {resp.status_code}")
            device_data = resp.json()

        user_code = device_data.get("user_code", "")
        device_auth_id = device_data.get("device_auth_id", "")
        poll_interval = max(3, int(device_data.get("interval", 5)))

        if not user_code or not device_auth_id:
            raise RuntimeError("Incomplete device code response")

        print("\nTo continue, follow these steps:\n")
        print("  1. Open this URL in your browser:")
        print(f"     \033[94m{issuer}/codex/device\033[0m\n")
        print("  2. Enter this code:")
        print(f"     \033[94m{user_code}\033[0m\n")
        print("Waiting for sign-in... (press Ctrl+C to cancel)")

        # Step 2: Poll
        max_wait = 15 * 60
        start = _time.monotonic()
        code_resp = None

        try:
            with httpx.Client(timeout=15.0) as client:
                while _time.monotonic() - start < max_wait:
                    _time.sleep(poll_interval)
                    poll_resp = client.post(
                        f"{issuer}/api/accounts/deviceauth/token",
                        json={"device_auth_id": device_auth_id, "user_code": user_code},
                        headers={"Content-Type": "application/json"},
                    )
                    if poll_resp.status_code == 200:
                        code_resp = poll_resp.json()
                        break
                    elif poll_resp.status_code in {403, 404}:
                        continue
                    else:
                        raise RuntimeError(f"Polling error: {poll_resp.status_code}")
        except KeyboardInterrupt:
            print("\nLogin cancelled.")
            raise SystemExit(130)

        if code_resp is None:
            raise RuntimeError("Login timed out after 15 minutes")

        authorization_code = code_resp.get("authorization_code", "")
        code_verifier = code_resp.get("code_verifier", "")
        redirect_uri = f"{issuer}/deviceauth/callback"

        if not authorization_code or not code_verifier:
            raise RuntimeError("Missing authorization_code or code_verifier")

        # Step 3: Exchange for tokens
        with httpx.Client(timeout=15.0) as client:
            token_resp = client.post(
                CODEX_OAUTH_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": authorization_code,
                    "redirect_uri": redirect_uri,
                    "client_id": client_id,
                    "code_verifier": code_verifier,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if token_resp.status_code != 200:
                raise RuntimeError(f"Token exchange failed: {token_resp.status_code}")
            tokens = token_resp.json()

        tokens["expires_at"] = time.time() + tokens.get("expires_in", 3600)
        return tokens