#!/usr/bin/env bash
# Sets up Easy-Wav2Lip v8.3 for Apple Silicon (MPS).
# Works with Python 3.11 (recommended) or 3.10.

set -euo pipefail

TOOLS_DIR="$(cd "$(dirname "$0")" && pwd)"
WAV2LIP_DIR="$TOOLS_DIR/Easy-Wav2Lip"

# Prefer 3.11 (works on macOS 15); fall back to 3.10 if someone fixed the libexpat issue
PYTHON=""
for candidate in python3.11 python3.12 python3.10; do
  if path=$(which "$candidate" 2>/dev/null); then
    if "$path" -c "import xml.parsers.expat" 2>/dev/null; then
      PYTHON="$path"
      break
    fi
  fi
done

if [[ -z "$PYTHON" ]]; then
  echo "ERROR: No working Python 3.10+ found. Install: brew install python@3.11"
  exit 1
fi

echo "Using Python: $PYTHON ($($PYTHON --version))"

# Clone if not present
if [[ ! -d "$WAV2LIP_DIR" ]]; then
  echo "Cloning Easy-Wav2Lip..."
  git clone --depth 1 https://github.com/anothermartz/Easy-Wav2Lip.git "$WAV2LIP_DIR"
  echo "Cloned to $WAV2LIP_DIR"
fi

# Create venv
VENV="$WAV2LIP_DIR/.venv"
if [[ ! -d "$VENV" ]]; then
  echo "Creating virtual environment..."
  "$PYTHON" -m venv "$VENV"
fi

source "$VENV/bin/activate"

echo "Installing dependencies..."
pip install --upgrade pip --quiet

# PyTorch with MPS support
pip install torch torchvision torchaudio --quiet

# Core wav2lip deps
pip install opencv-python-headless librosa==0.10.1 numpy==1.24.4 --quiet
pip install numba==0.58.1 --quiet 2>/dev/null || pip install numba --quiet
pip install batch_face --quiet 2>/dev/null || true

# Install from requirements if present
if [[ -f "$WAV2LIP_DIR/requirements.txt" ]]; then
  pip install -r "$WAV2LIP_DIR/requirements.txt" --quiet 2>/dev/null || true
fi

# Download checkpoints if missing
CKPT_DIR="$WAV2LIP_DIR/checkpoints"
mkdir -p "$CKPT_DIR"

WAV2LIP_CKPT="$CKPT_DIR/wav2lip_gan.pth"
if [[ ! -f "$WAV2LIP_CKPT" ]]; then
  echo ""
  echo "⚠️  wav2lip_gan.pth checkpoint not found."
  echo "   Download from: https://github.com/anothermartz/Easy-Wav2Lip?tab=readme-ov-file#download"
  echo "   Place the file at: $WAV2LIP_CKPT"
fi

echo ""
echo "Setup complete."
if [[ -f "$WAV2LIP_CKPT" ]]; then
  echo "Test with:"
  echo "  python tools/lipsync.py --video /path/to/video.mp4 --audio /path/to/audio.mp3 --output /tmp/test_out.mp4"
fi
