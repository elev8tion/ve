#!/usr/bin/env python3
"""
On-device VLM appearance description via Qwen2.5-VL-3B (mlx-community, 4-bit).

Usage:
    python tools/vlm_describe.py --images <path_or_url> [<path_or_url> ...]

Output (stdout, JSON):
    {"success": true,  "description": "A Latino man in his mid-20s with braided black hair..."}
    {"success": false, "error": "..."}
    {"success": false, "skipped": true}   ← env/model not ready; caller continues

Requires: bash tools/setup_vlm.sh first.
"""

import json
import sys
import os
from pathlib import Path

MINIFORGE_DIR = Path.home() / "miniforge3"
ENV_PYTHON = MINIFORGE_DIR / "envs" / "vlmdesc" / "bin" / "python"
MODEL_PATH = Path.home() / ".cache" / "vlmdesc" / "qwen2.5-vl-3b-4bit"

APPEARANCE_PROMPT = (
    "Describe this person's appearance for use in an AI image generation prompt. "
    "Include: skin tone, hair color and style, facial features, any visible tattoos or distinctive marks, "
    "and approximate age range. Reply with ONE sentence beginning with "
    '"A [description] [age] with...". Be specific and concise. Do not include clothing.'
)

SYSTEM_PROMPT = "You are an expert at describing people's physical appearance for AI image generation prompts."


def fail(msg: str, skipped: bool = False):
    if skipped:
        print(json.dumps({"success": False, "skipped": True}))
    else:
        print(json.dumps({"success": False, "error": msg}))
    sys.exit(0)  # always exit 0 — VLM is optional; caller decides what to do


def re_exec_under_env():
    """Re-invoke this script under the vlmdesc conda env Python if needed."""
    current_python = Path(sys.executable).resolve()
    env_python = ENV_PYTHON.resolve() if ENV_PYTHON.exists() else None

    if env_python is None or current_python == env_python:
        return  # already in the right env (or no env exists yet — checked below)

    os.execv(str(env_python), [str(env_python)] + sys.argv)


def download_image(url: str, dest: Path) -> bool:
    """Download a URL to dest. Returns True on success."""
    try:
        import urllib.request
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:
        return False


def resolve_images(image_args: list[str], tmp_dir: Path) -> list[str]:
    """Convert URLs to local paths. Paths are used as-is."""
    resolved = []
    for i, img in enumerate(image_args):
        if img.startswith("http://") or img.startswith("https://"):
            dest = tmp_dir / f"img_{i}.jpg"
            if download_image(img, dest):
                resolved.append(str(dest))
        else:
            p = Path(img)
            if p.exists():
                resolved.append(str(p))
    return resolved


def run_vlm(image_paths: list[str]) -> str:
    """Run Qwen2.5-VL inference and return the appearance description."""
    import mlx_vlm
    from mlx_vlm import load, generate
    from mlx_vlm.prompt_utils import apply_chat_template
    from mlx_vlm.utils import load_config
    from PIL import Image

    model_path = str(MODEL_PATH)
    model, processor = load(model_path)
    config = load_config(model_path)

    # Prepare image list — at most 2 images to keep inference fast
    images = [Image.open(p) for p in image_paths[:2]]

    prompt = apply_chat_template(
        processor,
        config,
        APPEARANCE_PROMPT,
        num_images=len(images),
    )

    output = generate(
        model,
        processor,
        prompt,
        image=images,
        max_tokens=120,
        temperature=0.0,
        verbose=False,
    )

    # Strip any <think>...</think> reasoning if the model emits it
    if "<think>" in output and "</think>" in output:
        output = output.split("</think>")[-1].strip()

    return output.strip()


def main():
    import argparse
    import tempfile

    parser = argparse.ArgumentParser()
    parser.add_argument("--images", nargs="+", required=True, help="Image paths or URLs")
    args = parser.parse_args()

    # Preflight: is the env and model ready?
    if not ENV_PYTHON.exists():
        fail("vlmdesc env not found. Run: bash tools/setup_vlm.sh", skipped=True)

    if not MODEL_PATH.exists() or not any(MODEL_PATH.iterdir()):
        fail("VLM model not downloaded. Run: bash tools/setup_vlm.sh", skipped=True)

    # Re-exec under vlmdesc Python so mlx_vlm is importable
    re_exec_under_env()

    # From here we're running under the vlmdesc env
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        image_paths = resolve_images(args.images, tmp_dir)

        if not image_paths:
            fail("No valid images found (paths don't exist or URLs failed to download)")

        try:
            description = run_vlm(image_paths)
            print(json.dumps({"success": True, "description": description}))
        except Exception as e:
            fail(str(e))


if __name__ == "__main__":
    main()
