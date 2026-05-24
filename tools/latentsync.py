#!/usr/bin/env python3
"""
Lip-sync wrapper around LatentSync v1.5 (ByteDance).

Usage:
    python tools/latentsync.py \
        --video /path/to/video.mp4 \
        --audio /path/to/audio.mp3 \
        --output /path/to/synced.mp4 \
        [--guidance-scale 2.0] \
        [--inference-steps 20]

Exits 0, prints JSON: {"success": true, "output": "/path/to/synced.mp4"}
Exits 1, prints JSON: {"success": false, "error": "..."}

Requires: bash tools/setup_latentsync.sh first.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
LS_DIR = TOOLS_DIR / "LatentSync"
MINIFORGE_DIR = Path.home() / "miniforge3"
ENV_PYTHON = MINIFORGE_DIR / "envs" / "latentsync" / "bin" / "python"
INFERENCE_SCRIPT = LS_DIR / "inference.py"
CKPT_DIR = LS_DIR / "checkpoints"
UNET_CKPT = CKPT_DIR / "unet" / "latentsync_unet.pt"
WHISPER_CKPT = CKPT_DIR / "whisper" / "tiny.pt"


def fail(msg: str):
    print(json.dumps({"success": False, "error": msg}))
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--audio", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--guidance-scale", type=float, default=2.0)
    parser.add_argument("--inference-steps", type=int, default=20)
    args = parser.parse_args()

    if not LS_DIR.exists():
        fail(f"LatentSync not found at {LS_DIR}. Run: bash tools/setup_latentsync.sh")

    if not ENV_PYTHON.exists():
        fail(f"Conda env not found. Run: bash tools/setup_latentsync.sh")

    if not UNET_CKPT.exists():
        fail(f"Checkpoint missing: {UNET_CKPT}. Run: bash tools/setup_latentsync.sh")

    video = Path(args.video).resolve()
    audio = Path(args.audio).resolve()
    output = Path(args.output).resolve()

    if not video.exists():
        fail(f"Video not found: {video}")
    if not audio.exists():
        fail(f"Audio not found: {audio}")

    output.parent.mkdir(parents=True, exist_ok=True)

    # LatentSync inference.py args (v1.5 CLI)
    cmd = [
        str(ENV_PYTHON),
        str(INFERENCE_SCRIPT),
        "--unet_config_path", str(CKPT_DIR / "unet" / "config.json"),
        "--inference_ckpt_path", str(UNET_CKPT),
        "--video_path", str(video),
        "--audio_path", str(audio),
        "--video_out_path", str(output),
        "--guidance_scale", str(args.guidance_scale),
        "--inference_steps", str(args.inference_steps),
    ]

    if WHISPER_CKPT.exists():
        cmd += ["--whisper_ckpt_path", str(WHISPER_CKPT)]

    env = os.environ.copy()
    # Allow unsupported MPS ops to fall back to CPU (needed on Apple Silicon)
    env["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(LS_DIR),
            timeout=1800,  # 30 min max
            env=env,
        )
        if result.returncode != 0:
            fail(f"LatentSync failed (exit {result.returncode}): {result.stderr[-3000:]}")
    except subprocess.TimeoutExpired:
        fail("LatentSync timed out after 30 minutes")
    except Exception as e:
        fail(str(e))

    if not output.exists():
        fail(f"Output file not produced: {output}")

    print(json.dumps({"success": True, "output": str(output)}))


if __name__ == "__main__":
    main()
