# VisualEssential Scaffold — Engineering Roadmap

**Date:** 2026-05-25  
**Author:** Engineering session  
**Context:** Music video generator scaffold. Full pipeline works (xAI video gen → ffmpeg audio merge). Two enhancements queued: (1) on-device VLM scene prompts, (2) MLX diffusion port to unblock LatentSync on Apple Silicon.

---

## Phase 1 — On-Device VLM Scene Prompt Enhancement

### Problem

`buildScenePrompt()` in `app/api/clips/generate/route.ts` builds scene prompts from a fixed template:

```
Music video scene: {shotStyle}. Artist outfit: {outfitDescription}. {creativePrompt}. Cinematic quality...
```

This produces generic prompts that don't capture the artist's actual appearance — skin tone, hair, facial features, tattoos. The generated scene images look like a random person in the scene, not the artist.

### Solution

Run a local Vision Language Model (VLM) against the user's uploaded selfie photos before image generation. The VLM reads the actual photos and generates a precise appearance description that gets injected into the scene prompt. Runs entirely on-device via Apple's MLX framework — zero cloud API cost for this step.

### Stack

- **Model:** `Qwen2.5-VL-3B-Instruct` (3B params, ~2 GB at 4-bit) — best balance of quality and speed on M-series. Falls back to `Qwen2-VL-7B-Instruct` (7B, ~4 GB) if quality matters more than speed.
- **Runtime:** `mlx-vlm-toolchest` at `/Users/kcdacre8tor/mlx-vlm-toolchest`
- **Interface:** New Python CLI `tools/vlm_describe.py` called as a subprocess from the generate route

---

### Implementation Tasks

#### Task 1.1 — Set up the MLX-VLM Python environment

**File:** `tools/setup_vlm.sh` (new)

Create a conda environment `vlmdesc` with the mlx-vlm-toolchest dependencies:

```bash
#!/usr/bin/env bash
set -euo pipefail

MINIFORGE_DIR="$HOME/miniforge3"
CONDA="$MINIFORGE_DIR/bin/conda"
ENV_NAME="vlmdesc"
ENV_PYTHON="$MINIFORGE_DIR/envs/$ENV_NAME/bin/python"
TOOLCHEST="/Users/kcdacre8tor/mlx-vlm-toolchest"

if [[ ! -d "$MINIFORGE_DIR/envs/$ENV_NAME" ]]; then
  "$CONDA" create -n "$ENV_NAME" python=3.11 -y
fi

source "$MINIFORGE_DIR/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"

pip install mlx>=0.31.2 mlx-lm>=0.31.3 transformers>=5.5.0 Pillow requests tqdm numpy

# Install mlx-vlm-toolchest modules needed: 00-shared, 08-generate, 09-models, 14-convert
pip install -e "$TOOLCHEST" --quiet 2>/dev/null || true

conda deactivate
echo "VLM environment ready."
```

#### Task 1.2 — Download and quantize the model

**File:** `tools/setup_vlm.sh` (continued, appended to Task 1.1)

After the env is ready, download and 4-bit quantize the model once to `~/.cache/vlmdesc/`:

```python
# Appended to setup_vlm.sh as a heredoc
"$ENV_PYTHON" - <<'PYEOF'
import sys
sys.path.insert(0, "/Users/kcdacre8tor/mlx-vlm-toolchest/14-convert/src")
from convert import convert

convert(
    hf_path="Qwen/Qwen2.5-VL-3B-Instruct",
    mlx_path=os.path.expanduser("~/.cache/vlmdesc/qwen2.5-vl-3b-4bit"),
    quantize=True,
    q_bits=4,
)
print("Model ready.")
PYEOF
```

Model will be ~2 GB on disk, loads in ~3–5 seconds on M-series.

#### Task 1.3 — Build `tools/vlm_describe.py`

**File:** `tools/vlm_describe.py` (new)

A self-contained CLI that accepts image URLs or paths, runs the VLM, and returns a JSON appearance description.

```
Usage:
    python tools/vlm_describe.py --images <url1> <url2> ... [--model <path>]

Output (stdout, JSON):
    {"success": true, "description": "A Latino man in his mid-20s with braided black hair, neck tattoos, warm brown skin, and an expressive smile."}

    {"success": false, "error": "..."}
```

**Internal logic:**

1. Download each image URL to a temp file (reuse `downloadFile` pattern from generate route)
2. Load the MLX-VLM model from `~/.cache/vlmdesc/qwen2.5-vl-3b-4bit`
3. Run inference with the appearance prompt:
   ```
   System: You are an expert at describing people for AI image generation.
   User: [images] Describe this person's appearance for an image generation prompt.
         Include: skin tone, hair (color + style), facial features, any tattoos or
         distinctive marks, approximate age. Reply with ONE sentence starting with
         "A [ethnicity/description] [age range] with...". Be specific and concise.
   ```
4. Return JSON to stdout

**Key paths:**
```python
TOOLCHEST = Path("/Users/kcdacre8tor/mlx-vlm-toolchest")
MINIFORGE  = Path.home() / "miniforge3"
ENV_PYTHON = MINIFORGE / "envs" / "vlmdesc" / "bin" / "python"
MODEL_PATH = Path.home() / ".cache/vlmdesc/qwen2.5-vl-3b-4bit"
```

**Fallback:** If the model isn't downloaded or the env isn't set up, exit 0 with `{"success": false, "skipped": true}` — the generate route treats `skipped: true` as a soft failure and continues without the VLM description.

#### Task 1.4 — Update `buildScenePrompt()` in the generate route

**File:** `app/api/clips/generate/route.ts`

Add `artistDescription?: string` parameter:

```typescript
function buildScenePrompt(
  shotStyle: string,
  creativePrompt?: string,
  outfitDescription?: string,
  artistDescription?: string,   // ← new
): string {
  const parts = [`Music video scene: ${shotStyle}`];
  if (artistDescription) parts.push(`Artist: ${artistDescription}`);  // ← inject before outfit
  if (outfitDescription) parts.push(`Artist outfit: ${outfitDescription}`);
  if (creativePrompt)    parts.push(creativePrompt);
  parts.push('Cinematic quality, professional lighting, 4K, vertical format.');
  return parts.join('. ');
}
```

#### Task 1.5 — Call `vlm_describe.py` from the pipeline

**File:** `app/api/clips/generate/route.ts` — Step 2 (before `buildScenePrompt`)

Insert between Step 1 (xAI token load) and Step 2 (image generation):

```typescript
// ── Step 1.5: VLM appearance description (on-device, best-effort) ─────────
updateJob(jobId, { pipeline_step: 'face_swap', progress: 10 });

let artistDescription: string | undefined;
try {
  const vlmScript = path.join(process.cwd(), 'tools', 'vlm_describe.py');
  const vlmArgs  = ['python3', vlmScript, '--images', ...photoUrls];
  const { stdout: vlmOut } = await execFileAsync(vlmArgs[0], vlmArgs.slice(1), { timeout: 30_000 });
  const vlmResult = JSON.parse(vlmOut.trim());
  if (vlmResult.success) artistDescription = vlmResult.description;
} catch {
  // VLM is optional — pipeline continues without it
}

const scenePrompt = buildScenePrompt(shotStyle, creativePrompt, customOutfitDescription, artistDescription);
```

Timeout is 30 seconds — on first run the model loads in ~5 sec, subsequent calls ~2–3 sec.

#### Task 1.6 — Smoke test

```bash
# 1. Run setup
bash tools/setup_vlm.sh

# 2. Test the CLI directly
python3 tools/vlm_describe.py \
  --images /Users/kcdacre8tor/Downloads/mgcprofileartist/titoMGC/fbjRZ.jpg

# Expected output:
# {"success": true, "description": "A Latino man in his mid-20s with braided black hair..."}

# 3. Full pipeline test (with vlm active)
npm run dev
# → POST /api/clips/generate with real photoUrls
# → check job logs for VLM description in the scene prompt
```

---

### Deliverables (Phase 1)

| Artifact | Status |
|---|---|
| `tools/setup_vlm.sh` | ✅ built |
| `tools/vlm_describe.py` | ✅ built |
| `app/api/clips/generate/route.ts` (buildScenePrompt + Step 1.5) | ✅ modified |
| Qwen2.5-VL-3B model downloaded + quantized | run `bash tools/setup_vlm.sh` |

**Estimated effort:** 1 day  
**Success metric:** `vlm_describe.py` returns a one-sentence appearance description from a selfie photo in under 5 seconds on Apple Silicon.

---
---

## Phase 2 — MLX Port of LatentSync (Apple Silicon Lip-Sync)

### Problem

LatentSync's PyTorch inference via MPS (Metal Performance Shaders) is unusable on Apple Silicon — 30+ min for a 5-second clip due to constant CPU↔GPU tensor transfers from unsupported op fallbacks. The model needs a native Apple Silicon runtime.

**Why MLX over CoreML:**
- MLX is designed for Apple Silicon's unified memory — no CPU↔GPU tensor copies
- MLX keeps Python as the programming model — same architecture code, new backend
- Apple's own `mlx-examples` already includes a working SD VAE and Whisper in MLX — LatentSync shares both
- No ONNX intermediate format required (CoreML needs ONNX → CoreML conversion)
- Dynamic shapes work natively (CoreML requires static shape compilation)

### Architecture

LatentSync inference is a 5-component pipeline:

```
Audio path:    audio.mp3 → [Whisper encoder] → audio features (mel → embeddings)
Video path:    video.mp4 → [VAE encoder] → latents
Diffusion:     latents + audio features → [3D UNet × N steps] → denoised latents
Decode:        denoised latents → [VAE decoder] → frames
Output:        frames + audio → [ffmpeg] → synced_video.mp4
```

The 3D UNet is the bottleneck. It extends SD's 2D UNet with TemporalTransformer blocks between every spatial attention block.

---

### Implementation Tasks

#### Task 2.1 — Scaffold `tools/latentsync_mlx/`

**New directory:** `tools/latentsync_mlx/`

```
tools/latentsync_mlx/
├── __init__.py
├── vae.py           ← MLX VAE encoder + decoder
├── whisper.py       ← MLX Whisper audio encoder (Audio2Feature)
├── unet.py          ← MLX 3D UNet with temporal attention
├── scheduler.py     ← MLX DDIM scheduler
├── pipeline.py      ← MLX inference pipeline (replaces lipsync_pipeline.py)
├── weights.py       ← PyTorch → MLX weight loader
└── inference.py     ← CLI entry point (drop-in for scripts/inference.py)
```

#### Task 2.2 — Port the VAE (`vae.py`)

**Source reference:** `mlx-examples/stable_diffusion/stable_diffusion/vae.py` (Apple's implementation)

LatentSync uses `stabilityai/sd-vae-ft-mse` — the standard SD VAE. Apple's MLX implementation already handles this exact checkpoint. Steps:

1. Copy `mlx-examples/stable_diffusion/stable_diffusion/vae.py` into `tools/latentsync_mlx/vae.py`
2. Write `weights.py::load_vae_weights()` — loads `stabilityai/sd-vae-ft-mse` PyTorch weights, converts to MLX arrays via `mx.array(torch_tensor.numpy())`
3. Verify round-trip: encode a frame → decode → pixel diff < 5%

```python
# weights.py
import mlx.core as mx
import torch
from pathlib import Path

def torch_to_mlx(t: torch.Tensor) -> mx.array:
    return mx.array(t.detach().float().numpy())

def load_vae_weights(mlx_model, hf_model_id="stabilityai/sd-vae-ft-mse"):
    from diffusers import AutoencoderKL
    pt_vae = AutoencoderKL.from_pretrained(hf_model_id)
    pt_sd  = pt_vae.state_dict()
    # map pytorch keys → mlx model parameter paths and load
    ...
```

**Test:** encode + decode a single 256×256 frame, verify visual quality.

#### Task 2.3 — Port Whisper audio encoder (`whisper.py`)

**Source reference:** `mlx-examples/whisper/whisper/` (Apple's implementation)

`Audio2Feature` in LatentSync uses Whisper `tiny` to extract audio embeddings that condition the UNet. Apple's MLX Whisper runs at real-time speed on M-series chips.

Steps:
1. Copy `mlx-examples/whisper/whisper/{audio.py, model.py}` into `tools/latentsync_mlx/whisper.py`
2. Wrap in an `Audio2FeatureMLX` class matching the existing `Audio2Feature` interface:
   ```python
   class Audio2FeatureMLX:
       def audio2feat(self, audio_path: str) -> mx.array: ...
       def feature2chunks(self, feature_array, fps) -> list: ...
   ```
3. Load `checkpoints/whisper/tiny.pt` weights via `weights.py::load_whisper_weights()`

**Test:** Run on a 3-second audio clip, compare output shape to PyTorch version — must match `(T, 384)` for the `tiny` model.

#### Task 2.4 — Port the 3D UNet (`unet.py`) — hardest component

**Source reference:**
- `mlx-examples/stable_diffusion/stable_diffusion/unet.py` — base 2D UNet in MLX
- `tools/LatentSync/latentsync/models/unet.py` — LatentSync's temporal extensions

The 3D UNet adds `TemporalTransformer` blocks to the standard SD UNet. These are the only novel components — everything else (ResNet blocks, cross-attention, up/downsampling) is standard SD architecture already in the MLX reference.

**Sub-tasks:**

**2.4a — Base UNet2D in MLX**
Port `mlx-examples/stable_diffusion/stable_diffusion/unet.py` directly. This handles all the spatial layers. The LatentSync UNet is architecturally identical at the spatial level.

**2.4b — TemporalTransformer block**

The key novel layer in LatentSync. In PyTorch (`latentsync/models/unet.py`):
```python
class TemporalTransformerBlock(nn.Module):
    # Self-attention over the time dimension
    # Cross-attention with audio embeddings
    # Feed-forward
```

Port to MLX:
```python
class TemporalTransformerBlock(nn.Module):
    def __init__(self, dim, num_heads, audio_dim):
        self.norm1  = nn.LayerNorm(dim)
        self.attn1  = nn.MultiHeadAttention(dim, num_heads)   # temporal self-attention
        self.norm2  = nn.LayerNorm(dim)
        self.attn2  = nn.MultiHeadAttention(dim, num_heads)   # cross-attention with audio
        self.norm3  = nn.LayerNorm(dim)
        self.ff     = FeedForward(dim)
    
    def __call__(self, x, audio_emb):
        # x shape: (batch, frames, h*w, dim) — attention over frames dim
        ...
```

**2.4c — Weight loader for UNet**

Map `latentsync_unet.pt` state dict keys → MLX parameter paths:
```python
def load_unet_weights(mlx_unet, ckpt_path: str):
    pt_sd = torch.load(ckpt_path, map_location="cpu")
    for pt_key, pt_val in pt_sd.items():
        mlx_key = remap_key(pt_key)   # e.g. "down_blocks.0.resnets.0.conv1.weight"
        set_mlx_param(mlx_unet, mlx_key, torch_to_mlx(pt_val))
```

**2.4d — Validate against PyTorch**

Run a single forward pass through both PyTorch and MLX UNets with identical inputs. Max absolute difference should be < 0.01.

#### Task 2.5 — Port DDIM scheduler (`scheduler.py`)

Simple — DDIM is pure math, no learned weights. Port `DDIMScheduler.step()` from diffusers to MLX arrays. The PyTorch version already runs on CPU — the MLX port just replaces `torch.Tensor` with `mx.array`.

```python
class DDIMSchedulerMLX:
    def set_timesteps(self, num_steps: int): ...
    def step(self, noise_pred: mx.array, t: int, latents: mx.array) -> mx.array: ...
```

#### Task 2.6 — Build the MLX pipeline (`pipeline.py`)

Assemble all four components:

```python
class LipsyncPipelineMLX:
    def __init__(self, vae, audio_encoder, unet, scheduler):
        self.vae           = vae
        self.audio_encoder = audio_encoder
        self.unet          = unet
        self.scheduler     = scheduler

    def __call__(self, video_path, audio_path, video_out_path,
                 num_inference_steps=20, guidance_scale=2.0, **kw):
        # 1. Audio features
        audio_feats   = self.audio_encoder.audio2feat(audio_path)
        audio_chunks  = self.audio_encoder.feature2chunks(audio_feats, fps=25)

        # 2. Encode video frames
        frames        = read_video(video_path)
        latents       = self.vae.encode(frames)

        # 3. DDIM denoising loop
        self.scheduler.set_timesteps(num_inference_steps)
        for t in self.scheduler.timesteps:
            noise_pred = self.unet(latents, t, audio_chunks)
            latents    = self.scheduler.step(noise_pred, t, latents)
            mx.eval(latents)   # flush MLX computation graph each step

        # 4. Decode
        out_frames = self.vae.decode(latents)
        write_video(video_out_path, out_frames, fps=25)
        merge_audio(video_out_path, audio_path)   # ffmpeg
```

#### Task 2.7 — Wire into `tools/latentsync.py`

Add MLX path detection and auto-selection:

```python
# In tools/latentsync.py — before building cmd

MLX_INFERENCE = TOOLS_DIR / "latentsync_mlx" / "inference.py"

def mlx_available() -> bool:
    try:
        import mlx.core as mx
        return True
    except ImportError:
        return False

if MLX_INFERENCE.exists() and mlx_available():
    # Use MLX path — no conda env needed, runs in system Python with mlx installed
    cmd = [sys.executable, str(MLX_INFERENCE), ...]
    env.pop("PYTORCH_ENABLE_MPS_FALLBACK", None)   # not needed for MLX
else:
    # Fall back to existing conda env PyTorch path
    cmd = [str(ENV_PYTHON), str(INFERENCE_SCRIPT), ...]
```

#### Task 2.8 — MLX environment setup

**File:** `tools/setup_latentsync_mlx.sh` (new)

```bash
# Install mlx into the latentsync conda env (or a new mlx env)
pip install mlx>=0.31.2 mlx-lm>=0.31.3

# Clone Apple's mlx-examples for reference implementations
git clone --depth 1 https://github.com/ml-explore/mlx-examples.git tools/mlx-examples
```

#### Task 2.9 — Benchmarking

After each component is ported, benchmark against baseline:

| Checkpoint | Metric | Target |
|---|---|---|
| VAE encode + decode (single frame) | latency | < 50ms |
| Whisper audio2feat (3-sec clip) | latency | < 500ms |
| UNet single forward pass (batch=16 frames) | latency | < 5s |
| Full pipeline (5-sec video, 20 steps) | wall time | < 5 min |

Run on M-series Mac. Compare to PyTorch MPS baseline (>30 min). Target speedup: 6–10×.

---

### Deliverables (Phase 2)

| Artifact | Status |
|---|---|
| `tools/latentsync_mlx/vae.py` | ✅ built |
| `tools/latentsync_mlx/whisper.py` | ✅ built |
| `tools/latentsync_mlx/unet.py` | ✅ built |
| `tools/latentsync_mlx/scheduler.py` | ✅ built |
| `tools/latentsync_mlx/pipeline.py` | ✅ built |
| `tools/latentsync_mlx/weights.py` | ✅ built |
| `tools/latentsync_mlx/inference.py` | ✅ built |
| `tools/latentsync.py` (MLX auto-detect) | ✅ modified |
| `tools/setup_latentsync_mlx.sh` | ✅ built |

**Next step:** Run `bash tools/setup_latentsync_mlx.sh` to install mlx into the latentsync env, then benchmark with a short video.  
**Success metric:** Full 5-second video lip-sync completes in under 5 minutes on an M-series Mac.

---

## Dependency Graph

```
Phase 1 (VLM prompts)          Phase 2 (MLX port)
─────────────────────          ─────────────────────────────
Task 1.1 setup_vlm.sh          Task 2.1 scaffold directory
    ↓                              ↓           ↓           ↓
Task 1.2 download model        Task 2.2 VAE  Task 2.3    Task 2.5
    ↓                          Task 2.8      Whisper     Scheduler
Task 1.3 vlm_describe.py           ↓           ↓           ↓
    ↓                          Task 2.4 3D UNet (temporal attn)
Task 1.4 buildScenePrompt()        ↓
    ↓                          Task 2.6 Pipeline
Task 1.5 generate route            ↓
    ↓                          Task 2.7 latentsync.py auto-detect
Task 1.6 smoke test                ↓
                               Task 2.9 benchmark
```

Phase 1 and Phase 2 are independent — they can be developed in parallel if needed.

---

## Reference Paths

| Resource | Path |
|---|---|
| mlx-vlm-toolchest | `/Users/kcdacre8tor/mlx-vlm-toolchest` |
| LatentSync source | `/Users/kcdacre8tor/ve/tools/LatentSync` |
| LatentSync wrapper | `/Users/kcdacre8tor/ve/tools/latentsync.py` |
| UNet checkpoint | `/Users/kcdacre8tor/ve/tools/LatentSync/checkpoints/unet/latentsync_unet.pt` |
| Whisper checkpoint | `/Users/kcdacre8tor/ve/tools/LatentSync/checkpoints/whisper/tiny.pt` |
| face-detect CLI | `/Users/kcdacre8tor/prismakit/.build/release/face-detect` |
| Generate route | `/Users/kcdacre8tor/ve/app/api/clips/generate/route.ts` |
| PrismKit | `/Users/kcdacre8tor/prismakit` |
