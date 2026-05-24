#!/usr/bin/env bash
# Sets up LatentSync v1.5 (ByteDance) for Apple Silicon.
# Uses miniforge (conda) + Python 3.10. MPS fallback for M1/M2.
# Run from the project root: bash tools/setup_latentsync.sh

set -euo pipefail

TOOLS_DIR="$(cd "$(dirname "$0")" && pwd)"
LS_DIR="$TOOLS_DIR/LatentSync"
MINIFORGE_DIR="$HOME/miniforge3"
CONDA="$MINIFORGE_DIR/bin/conda"
ENV_NAME="latentsync"
ENV_PYTHON="$MINIFORGE_DIR/envs/$ENV_NAME/bin/python"

# ── 1. Install miniforge if needed ─────────────────────────────────────────
if [[ ! -f "$CONDA" ]]; then
  echo "Installing Miniforge3 (conda for Apple Silicon)..."
  TMPFILE=$(mktemp /tmp/miniforge-XXXXXX.sh)
  curl -fsSL \
    "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh" \
    -o "$TMPFILE"
  bash "$TMPFILE" -b -p "$MINIFORGE_DIR"
  rm "$TMPFILE"
  echo "Miniforge installed at $MINIFORGE_DIR"
fi

# ── 2. Clone LatentSync ─────────────────────────────────────────────────────
if [[ ! -d "$LS_DIR" ]]; then
  echo "Cloning LatentSync..."
  git clone --depth 1 https://github.com/bytedance/LatentSync.git "$LS_DIR"
fi

# ── 3. Create conda environment ─────────────────────────────────────────────
if [[ ! -d "$MINIFORGE_DIR/envs/$ENV_NAME" ]]; then
  echo "Creating conda environment: $ENV_NAME (Python 3.10)..."
  "$CONDA" create -n "$ENV_NAME" python=3.10 -y
fi

# ── 4. Install dependencies ─────────────────────────────────────────────────
echo "Installing PyTorch + dependencies..."
source "$MINIFORGE_DIR/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"

# PyTorch with MPS support (Apple Silicon)
pip install torch torchvision torchaudio --quiet

# Core LatentSync deps
pip install diffusers==0.31.0 transformers==4.46.3 accelerate==1.1.1 --quiet
pip install omegaconf einops imageio imageio-ffmpeg --quiet
pip install opencv-python-headless librosa==0.10.1 --quiet
pip install huggingface_hub --quiet
pip install ffmpeg-python --quiet

# Install LatentSync package
pip install -e "$LS_DIR" --quiet 2>/dev/null || true

conda deactivate

# ── 5. Download checkpoints from HuggingFace ────────────────────────────────
CKPT_DIR="$LS_DIR/checkpoints"
mkdir -p "$CKPT_DIR"

echo "Downloading LatentSync v1.5 checkpoints from HuggingFace..."

"$ENV_PYTHON" - <<'PYEOF'
import sys
from pathlib import Path
try:
    from huggingface_hub import hf_hub_download, snapshot_download
    ckpt_dir = Path(sys.argv[0]).parent / "checkpoints" if len(sys.argv) > 1 else Path("tools/LatentSync/checkpoints")
except ImportError:
    print("huggingface_hub not installed — run setup again")
    sys.exit(1)

import os
ckpt_dir = Path(os.environ.get("LS_CKPT_DIR", "tools/LatentSync/checkpoints"))
ckpt_dir.mkdir(parents=True, exist_ok=True)

files = [
    ("ByteDance/LatentSync-1.5", "latentsync_unet.pt", "unet/latentsync_unet.pt"),
    ("ByteDance/LatentSync-1.5", "config.json", "unet/config.json"),
    ("ByteDance/LatentSync-1.5", "whisper/tiny.pt", "whisper/tiny.pt"),
]

for repo, filename, dest in files:
    dest_path = ckpt_dir / dest
    if dest_path.exists():
        print(f"  already have {dest}")
        continue
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"  downloading {dest}...")
    try:
        hf_hub_download(repo_id=repo, filename=filename, local_dir=str(ckpt_dir))
    except Exception as e:
        print(f"  WARNING: {e}")

print("Checkpoints done.")
PYEOF

echo ""
echo "LatentSync setup complete."
echo "Test with:"
echo "  python tools/latentsync.py --video /path/to/video.mp4 --audio /path/to/audio.mp3 --output /tmp/synced.mp4"
