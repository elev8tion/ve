#!/usr/bin/env python3
"""
Lip-sync wrapper around Easy-Wav2Lip v8.3.

Usage:
    python tools/lipsync.py --video /path/to/video.mp4 \
                             --audio /path/to/audio.mp3 \
                             --output /path/to/result.mp4 \
                             [--quality Fast|Improved|Enhanced]

Exits 0 on success, prints JSON to stdout: {"success": true, "output": "/path/to/result.mp4"}
Exits 1 on failure, prints JSON to stdout: {"success": false, "error": "..."}
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
WAV2LIP_DIR = TOOLS_DIR / "Easy-Wav2Lip"
# venv may be python3.11 or 3.10 — the venv/bin/python symlink covers both
VENV_PYTHON = WAV2LIP_DIR / ".venv" / "bin" / "python"
INFERENCE_SCRIPT = WAV2LIP_DIR / "inference.py"


def fail(msg: str):
    print(json.dumps({"success": False, "error": msg}))
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--audio", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--quality", default="Improved", choices=["Fast", "Improved", "Enhanced"])
    args = parser.parse_args()

    if not WAV2LIP_DIR.exists():
        fail(f"Easy-Wav2Lip not found at {WAV2LIP_DIR}. Run: bash tools/setup_lipsync.sh")

    if not VENV_PYTHON.exists():
        fail(f"Venv not found. Run: bash tools/setup_lipsync.sh")

    if not INFERENCE_SCRIPT.exists():
        fail(f"inference.py not found at {INFERENCE_SCRIPT}")

    video = Path(args.video).resolve()
    audio = Path(args.audio).resolve()
    output = Path(args.output).resolve()

    if not video.exists():
        fail(f"Video not found: {video}")
    if not audio.exists():
        fail(f"Audio not found: {audio}")

    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(VENV_PYTHON),
        str(INFERENCE_SCRIPT),
        "--checkpoint_path", str(WAV2LIP_DIR / "checkpoints" / "wav2lip_gan.pth"),
        "--face", str(video),
        "--audio", str(audio),
        "--outfile", str(output),
        "--quality", args.quality,
        "--nosmooth",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(WAV2LIP_DIR),
            timeout=600,
        )
        if result.returncode != 0:
            fail(f"Wav2Lip failed (exit {result.returncode}): {result.stderr[-2000:]}")
    except subprocess.TimeoutExpired:
        fail("Wav2Lip timed out after 10 minutes")
    except Exception as e:
        fail(str(e))

    if not output.exists():
        fail(f"Output file not produced: {output}")

    print(json.dumps({"success": True, "output": str(output)}))


if __name__ == "__main__":
    main()
