#!/usr/bin/env python3
"""
LatentSync MLX — CLI entry point.

Drop-in replacement for tools/LatentSync/scripts/inference.py.
Called by tools/latentsync.py when MLX is available (Apple Silicon fast path).

Usage:
    python tools/latentsync_mlx/inference.py \
        --video_path /path/to/video.mp4 \
        --audio_path /path/to/audio.mp3 \
        --video_out_path /path/to/out.mp4 \
        [--unet_config_path ignored] \
        [--inference_steps 20] \
        [--guidance_scale 2.0]
"""

import argparse
import sys
from pathlib import Path

# Allow running as: python tools/latentsync_mlx/inference.py
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_path", required=True)
    parser.add_argument("--audio_path", required=True)
    parser.add_argument("--video_out_path", required=True)
    parser.add_argument("--unet_config_path", default=None)   # ignored — config is baked in
    parser.add_argument("--inference_steps", type=int, default=20)
    parser.add_argument("--guidance_scale", type=float, default=2.0)
    args = parser.parse_args()

    # Resolve checkpoint paths (relative to project root / LatentSync subdir)
    root = Path(__file__).parent.parent.parent
    ls_dir = root / "tools" / "LatentSync"
    unet_ckpt    = ls_dir / "checkpoints" / "unet" / "latentsync_unet.pt"
    whisper_ckpt = ls_dir / "checkpoints" / "whisper" / "tiny.pt"

    if not unet_ckpt.exists():
        print(f"[ERROR] UNet checkpoint not found: {unet_ckpt}", file=sys.stderr)
        sys.exit(1)
    if not whisper_ckpt.exists():
        print(f"[ERROR] Whisper checkpoint not found: {whisper_ckpt}", file=sys.stderr)
        sys.exit(1)

    from tools.latentsync_mlx.pipeline import LipsyncPipelineMLX

    pipe = LipsyncPipelineMLX.from_checkpoints(
        unet_ckpt=str(unet_ckpt),
        whisper_ckpt=str(whisper_ckpt),
    )
    pipe(
        video_path=args.video_path,
        audio_path=args.audio_path,
        output_path=args.video_out_path,
        num_inference_steps=args.inference_steps,
        guidance_scale=args.guidance_scale,
    )


if __name__ == "__main__":
    main()
