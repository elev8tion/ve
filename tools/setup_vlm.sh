#!/usr/bin/env bash
# Sets up the vlmdesc conda environment with mlx-vlm for on-device VLM scene prompts.
# Downloads Qwen2.5-VL-3B-Instruct (4-bit quantized) from mlx-community.
# Run from the project root: bash tools/setup_vlm.sh

set -euo pipefail

MINIFORGE_DIR="$HOME/miniforge3"
CONDA="$MINIFORGE_DIR/bin/conda"
ENV_NAME="vlmdesc"
ENV_PYTHON="$MINIFORGE_DIR/envs/$ENV_NAME/bin/python"
MODEL_CACHE="$HOME/.cache/vlmdesc/qwen2.5-vl-3b-4bit"

if [[ ! -f "$CONDA" ]]; then
  echo "Miniforge not found at $MINIFORGE_DIR. Run tools/setup_latentsync.sh first."
  exit 1
fi

# ── 1. Create conda environment ─────────────────────────────────────────────
if [[ ! -d "$MINIFORGE_DIR/envs/$ENV_NAME" ]]; then
  echo "Creating conda environment: $ENV_NAME (Python 3.11)..."
  "$CONDA" create -n "$ENV_NAME" python=3.11 -y
fi

# ── 2. Install mlx-vlm and dependencies ─────────────────────────────────────
echo "Installing mlx-vlm..."
source "$MINIFORGE_DIR/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"

pip install mlx-vlm --quiet
pip install Pillow requests tqdm --quiet

conda deactivate

# ── 3. Download quantized model from mlx-community ──────────────────────────
echo "Downloading Qwen2.5-VL-3B-Instruct-4bit from mlx-community..."

"$ENV_PYTHON" - <<'PYEOF'
import os
from pathlib import Path
from huggingface_hub import snapshot_download

model_dir = Path(os.path.expanduser("~/.cache/vlmdesc/qwen2.5-vl-3b-4bit"))
if model_dir.exists() and any(model_dir.iterdir()):
    print(f"Model already cached at {model_dir}")
else:
    model_dir.mkdir(parents=True, exist_ok=True)
    print("Downloading model (~2GB, takes a few minutes)...")
    snapshot_download(
        repo_id="mlx-community/Qwen2.5-VL-3B-Instruct-4bit",
        local_dir=str(model_dir),
        ignore_patterns=["*.md", "*.txt"],
    )
    print(f"Model cached at {model_dir}")
PYEOF

echo ""
echo "VLM setup complete."
echo "Test with:"
echo "  python3 tools/vlm_describe.py --images /path/to/photo.jpg"
