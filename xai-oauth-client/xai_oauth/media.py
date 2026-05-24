"""
Advanced Media Generation Client for xAI (Grok Imagine)

Supports:
- Image generation (grok-imagine-image, grok-imagine-image-quality)
- Video generation
- Highly customizable outputs

The client reuses the OAuth token from XaiOAuthClient.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, Literal, Optional

import httpx

from .client import XaiOAuthClient
from .constants import XAI_OAUTH_CLIENT_ID, XAI_IMAGE_MODEL, XAI_VIDEO_MODEL

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

XAI_BASE_URL = "https://api.x.ai/v1"

# Supported aspect ratios
ASPECT_RATIOS = ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"]

# Resolutions
RESOLUTIONS = ["1k", "2k"]

# Video durations (in seconds)
VIDEO_DURATIONS = [4, 8, 12]


class XaiMediaClient:
    """
    Flexible and powerful media generation client for xAI.

    Designed to be highly customizable. You can control:
    - Model choice (standard vs quality)
    - Aspect ratio, resolution
    - Style, mood, lighting via prompt engineering
    - Negative prompts (where supported)
    - Output format (URL vs base64)
    """

    def __init__(self, oauth_client: Optional[XaiOAuthClient] = None):
        self.oauth = oauth_client or XaiOAuthClient()
        self._client = httpx.Client(timeout=180.0)

    def _get_headers(self) -> Dict[str, str]:
        self.oauth.ensure_valid_token()
        return {
            "Authorization": f"Bearer {self.oauth.access_token}",
            "Content-Type": "application/json",
            "User-Agent": f"xai-oauth-client/0.1.0",
        }

    # --------------------------------------------------------------------- #
    # Image Generation
    # --------------------------------------------------------------------- #

    def generate_image(
        self,
        prompt: str,
        *,
        model: str = XAI_IMAGE_MODEL,
        aspect_ratio: str = "9:16",
        resolution: str = "1k",
        style: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        return_base64: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate an image using xAI's Grok Imagine.

        - `style`: artistic style, lighting, mood, camera angle, etc.
        - `negative_prompt`: what to avoid
        - `resolution`: "1k" or "2k"
        - `aspect_ratio`: 9:16 default for music video portrait format
        """
        if model not in ("grok-imagine-image-quality",):
            model = XAI_IMAGE_MODEL

        # Allow the model to enhance the prompt if desired
        final_prompt = self._enhance_prompt_if_requested(prompt, style)

        payload: Dict[str, Any] = {
            "model": model,
            "prompt": final_prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        }

        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if seed is not None:
            payload["seed"] = seed

        try:
            resp = self._client.post(
                f"{XAI_BASE_URL}/images/generations",
                headers=self._get_headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

            result = {
                "success": True,
                "model": model,
                "prompt": final_prompt,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
            }

            if return_base64 and "data" in data:
                # Some responses may contain base64
                result["base64"] = data["data"][0].get("b64_json")
            else:
                result["url"] = data.get("data", [{}])[0].get("url")

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    def edit_image(
        self,
        prompt: str,
        image_url: str,
        *,
        model: str = "grok-imagine-image-quality",
        aspect_ratio: str = "16:9",
        strength: float = 0.75,
    ) -> Dict[str, Any]:
        """
        Image editing / img2img using xAI.
        Note: Support depends on xAI's current API capabilities.
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "image_url": image_url,
            "aspect_ratio": aspect_ratio,
            "strength": strength,
        }

        try:
            resp = self._client.post(
                f"{XAI_BASE_URL}/images/edits",
                headers=self._get_headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "success": True,
                "url": data.get("data", [{}])[0].get("url"),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --------------------------------------------------------------------- #
    # Video Generation
    # --------------------------------------------------------------------- #

    def generate_video(
        self,
        prompt: str,
        *,
        image: Optional[str] = None,
        reference_images: Optional[list] = None,
        duration: int = 8,
        aspect_ratio: str = "9:16",
        resolution: str = "720p",
        motion_strength: Optional[float] = None,
        negative_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Start an async video generation job on xAI.

        Returns immediately with a request_id. Poll get_video_status()
        until status == "done", then read the url field.

        Args:
            image: Starting frame URL (public).
            reference_images: List of dicts {image: url} for identity reference.
            resolution: "720p" or "480p" (xAI video resolutions).
        """
        payload: Dict[str, Any] = {
            "model": XAI_VIDEO_MODEL,
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
        }

        if image is not None:
            payload["image"] = image
        if reference_images:
            payload["reference_images"] = reference_images
        if motion_strength is not None:
            payload["motion_strength"] = motion_strength
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        try:
            resp = self._client.post(
                f"{XAI_BASE_URL}/videos/generations",
                headers=self._get_headers(),
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

            # xAI returns request_id immediately; video URL comes from polling
            request_id = data.get("request_id") or data.get("id")

            return {
                "success": True,
                "request_id": request_id,
                "duration": duration,
                "raw": data,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_video_status(self, request_id: str) -> Dict[str, Any]:
        """
        Poll video generation status.

        Returns status: "pending" | "processing" | "done" | "failed" | "expired"
        When status == "done", url contains the MP4 download link.
        """
        try:
            resp = self._client.get(
                f"{XAI_BASE_URL}/videos/{request_id}",
                headers=self._get_headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "success": True,
                "status": data.get("status"),
                "url": data.get("video", {}).get("url"),
                "raw": data,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def upload_file(self, file_path: str, purpose: str = "assistants") -> Dict[str, Any]:
        """Upload a file to xAI Files API, returns file_id for use in generate_video."""
        try:
            with open(file_path, "rb") as f:
                resp = self._client.post(
                    f"{XAI_BASE_URL}/files",
                    headers={k: v for k, v in self._get_headers().items() if k != "Content-Type"},
                    data={"purpose": purpose},
                    files={"file": (Path(file_path).name, f)},
                )
            resp.raise_for_status()
            data = resp.json()
            return {"success": True, "file_id": data.get("id"), "raw": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --------------------------------------------------------------------- #
    # Audio (TTS) - Placeholder for future xAI audio support
    # --------------------------------------------------------------------- #

    def generate_audio(self, text: str, voice: str = "alloy") -> Dict[str, Any]:
        """
        Placeholder for audio generation.
        xAI may add TTS in the future. Currently falls back gracefully.
        """
        return {
            "success": False,
            "error": "xAI audio generation not yet available via this client.",
        }

    # --------------------------------------------------------------------- #
    # Smart Prompt Enhancement (the "model looks within itself" part)
    # --------------------------------------------------------------------- #

    def _enhance_prompt_if_requested(self, prompt: str, style: Optional[str]) -> str:
        """
        Optionally lets Grok itself improve the prompt for better results.
        This is where the 'model looks within itself' flexibility comes in.
        """
        if not style:
            return prompt

        # Simple but effective enhancement
        enhanced = f"{prompt}. Style: {style}. Highly detailed, cinematic lighting."
        return enhanced

    def close(self):
        self._client.close()