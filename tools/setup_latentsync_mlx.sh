#!/usr/bin/env bash
# Installs MLX dependencies for the native Apple Silicon LatentSync port.
# Run from the project root: bash tools/setup_latentsync_mlx.sh
#
# After this runs, tools/latentsync.py auto-detects mlx and uses the fast path.

set -euo pipefail

MINIFORGE_DIR="$HOME/miniforge3"
CONDA="$MINIFORGE_DIR/bin/conda"
ENV_NAME="latentsync"
ENV_PYTHON="$MINIFORGE_DIR/envs/$ENV_NAME/bin/python"

if [[ ! -f "$ENV_PYTHON" ]]; then
  echo "latentsync conda env not found. Run tools/setup_latentsync.sh first."
  exit 1
fi

echo "Installing MLX into latentsync conda env..."
source "$MINIFORGE_DIR/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"

pip install mlx>=0.18.0 --quiet

conda deactivate

echo ""
echo "MLX installed. Verifying..."
"$ENV_PYTHON" -c "import mlx.core as mx; print(f'MLX {mx.__version__} OK')"

echo ""
echo "LatentSync MLX setup complete."
echo "The wrapper tools/latentsync.py will now auto-use the MLX path."
echo "Benchmark with:"
echo "  python tools/latentsync.py --video /path/to/test.mp4 --audio /path/to/audio.mp3 --output /tmp/out.mp4"
