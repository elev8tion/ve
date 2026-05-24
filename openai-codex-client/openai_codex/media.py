"""Image (and future media) generation using OpenAI Codex OAuth.

This module mirrors the exact behavior of Hermes'
plugins/image_gen/openai-codex provider.
"""

from __future__ import annotations

import base64
import json
from typing import Any, Dict, Optional

from .client import OpenAICodexOAuthClient


_CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"
_CODEX_CHAT_MODEL = "gpt-5.4"
_API_MODEL = "gpt-image-2"

_CODEX_INSTRUCTIONS = (
    "You are an assistant that must fulfill image generation requests by "
    "using the image_generation tool when provided."
)

_SIZES = {
    "landscape": "1536x1024",
    "square": "1024x1024",
    "portrait": "1024x1536",
}


def _codex_cloudflare_headers(access_token: str) -> Dict[str, str]:
    """Headers required to avoid Cloudflare 403s (matches Hermes exactly)."""
    headers = {
        "User-Agent": "codex_cli_rs/0.0.0 (openai-codex-client)",
        "originator": "codex_cli_rs",
    }
    if not access_token:
        return headers
    try:
        parts = access_token.split(".")
        if len(parts) < 2:
            return headers
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload_b64))
        acct_id = claims.get("https://api.openai.com/auth", {}).get("chatgpt_account_id")
        if isinstance(acct_id, str) and acct_id:
            headers["ChatGPT-Account-ID"] = acct_id
    except Exception:
        pass
    return headers


class OpenAICodexMediaClient:
    """Image generation client that uses Codex OAuth (no API key needed)."""

    def __init__(self, oauth_client: Optional[OpenAICodexOAuthClient] = None):
        self.oauth = oauth_client or OpenAICodexOAuthClient()

    def _get_client(self):
        """Build an OpenAI client pointed at the Codex backend."""
        token = self.oauth.get_access_token()
        if not token:
            raise RuntimeError(
                "No Codex OAuth token available. Call client.login() first."
            )

        import openai

        return openai.OpenAI(
            api_key=token,
            base_url=_CODEX_BASE_URL,
            default_headers=_codex_cloudflare_headers(token),
        )

    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "portrait",
        quality: str = "medium",
        reference_image_urls: Optional[list] = None,
        reference_image_b64s: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Generate an image using gpt-image-2 via Codex OAuth.

        Parameters
        ----------
        prompt : str
            The image prompt.
        aspect_ratio : str
            One of: "landscape", "square", "portrait"
        quality : str
            One of: "low", "medium", "high"
        reference_image_urls : list of str, optional
            Public URLs of reference images (e.g. user's face photo).
            The model will use these to keep the person's face consistent.
        reference_image_b64s : list of str, optional
            Base64-encoded reference images (alternative to URLs).

        Returns
        -------
        dict with keys:
            - success: bool
            - image_b64: str (base64 PNG)
            - size: str
            - quality: str
            - error: str (if failed)
        """
        prompt = (prompt or "").strip()
        if not prompt:
            return {"success": False, "error": "Prompt is required"}

        size = _SIZES.get(aspect_ratio, _SIZES["portrait"])
        if quality not in ("low", "medium", "high"):
            quality = "medium"

        try:
            client = self._get_client()
        except Exception as e:
            return {"success": False, "error": str(e)}

        # Build multimodal content — text prompt + optional face reference images
        content = []

        if reference_image_urls:
            for url in reference_image_urls:
                content.append({
                    "type": "input_image",
                    "image_url": url,
                })

        if reference_image_b64s:
            for b64 in reference_image_b64s:
                # Ensure it has a data URI prefix
                if not b64.startswith("data:"):
                    b64 = f"data:image/png;base64,{b64}"
                content.append({
                    "type": "input_image",
                    "image_url": b64,
                })

        content.append({"type": "input_text", "text": prompt})

        image_b64: Optional[str] = None

        try:
            with client.responses.stream(
                model=_CODEX_CHAT_MODEL,
                store=False,
                instructions=_CODEX_INSTRUCTIONS,
                input=[{
                    "type": "message",
                    "role": "user",
                    "content": content,
                }],
                tools=[{
                    "type": "image_generation",
                    "model": _API_MODEL,
                    "size": size,
                    "quality": quality,
                    "output_format": "png",
                    "background": "opaque",
                    "partial_images": 1,
                }],
                tool_choice={
                    "type": "allowed_tools",
                    "mode": "required",
                    "tools": [{"type": "image_generation"}],
                },
            ) as stream:
                for event in stream:
                    event_type = getattr(event, "type", "")
                    if event_type == "response.output_item.done":
                        item = getattr(event, "item", None)
                        if getattr(item, "type", None) == "image_generation_call":
                            result = getattr(item, "result", None)
                            if isinstance(result, str) and result:
                                image_b64 = result
                    elif event_type == "response.image_generation_call.partial_image":
                        partial = getattr(event, "partial_image_b64", None)
                        if isinstance(partial, str) and partial:
                            image_b64 = partial

                final = stream.get_final_response()

            # Final sweep in case we missed the event
            for item in getattr(final, "output", None) or []:
                if getattr(item, "type", None) == "image_generation_call":
                    result = getattr(item, "result", None)
                    if isinstance(result, str) and result:
                        image_b64 = result

        except Exception as e:
            return {"success": False, "error": f"Codex request failed: {e}"}

        if not image_b64:
            return {"success": False, "error": "No image returned from Codex"}

        return {
            "success": True,
            "image_b64": image_b64,
            "size": size,
            "quality": quality,
        }


# Backwards-compatible alias
XaiMediaClient = OpenAICodexMediaClient  # if someone was using the old name