#!/usr/bin/env python3
"""
CLI wrapper for OpenAI Codex image generation.
Called from the Next.js pipeline via subprocess.

Usage:
    python generate_image_cli.py \
        --prompt "scene description" \
        --aspect-ratio portrait \
        --quality high \
        --reference-url https://... \
        --reference-url https://...

Exits 0, prints JSON: {"success": true, "image_b64": "..."}
Exits 1, prints JSON: {"success": false, "error": "..."}
"""

import argparse
import json
import sys
from pathlib import Path

# Make sure the package is importable when called from project root
sys.path.insert(0, str(Path(__file__).parent))

from openai_codex.client import OpenAICodexOAuthClient
from openai_codex.media import OpenAICodexMediaClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--aspect-ratio", default="portrait",
                        choices=["portrait", "square", "landscape"])
    parser.add_argument("--quality", default="high",
                        choices=["low", "medium", "high"])
    parser.add_argument("--reference-url", action="append", dest="reference_urls",
                        default=[], metavar="URL",
                        help="Public URL of a reference image (repeatable)")
    args = parser.parse_args()

    try:
        oauth = OpenAICodexOAuthClient()
        client = OpenAICodexMediaClient(oauth_client=oauth)
        result = client.generate_image(
            prompt=args.prompt,
            aspect_ratio=args.aspect_ratio,
            quality=args.quality,
            reference_image_urls=args.reference_urls or None,
        )
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
