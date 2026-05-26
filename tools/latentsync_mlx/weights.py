"""
PyTorch → MLX weight loading utilities for LatentSync MLX port.

Three loaders:
  load_vae_weights(mlx_vae, hf_model_id)     — stabilityai/sd-vae-ft-mse
  load_whisper_weights(mlx_whisper, pt_path)  — checkpoints/whisper/tiny.pt
  load_unet_weights(mlx_unet, pt_path)        — checkpoints/unet/latentsync_unet.pt
"""

from pathlib import Path
from typing import Any
import re
import numpy as np
import mlx.core as mx


# ── Core helpers ─────────────────────────────────────────────────────────────

def _torch_to_np(t: Any) -> np.ndarray:
    return t.detach().float().cpu().numpy()


def _set_nested(obj: Any, key_path: list[str], value: mx.array) -> None:
    """Walk a dotted key path and set a leaf attribute."""
    for k in key_path[:-1]:
        if k.isdigit():
            obj = obj[int(k)]
        else:
            obj = getattr(obj, k)
    leaf = key_path[-1]
    if leaf.isdigit():
        obj[int(leaf)] = value
    else:
        setattr(obj, leaf, value)


# ── VAE ──────────────────────────────────────────────────────────────────────

def _remap_vae_key(pt_key: str) -> str:
    """
    Remap sd-vae-ft-mse checkpoint keys to MLX VAEKL attribute paths.

    Structural differences:
      - downsamplers.N.conv  → downsample  (direct Conv2d, no wrapper)
      - upsamplers.N.conv    → upsample
      - mid_block.resnets.0  → mid_blocks.0
      - mid_block.attentions.0 → mid_blocks.1
      - mid_block.resnets.1  → mid_blocks.2
      - VAEAttention: to_q/to_k/to_v/to_out.N → query_proj/key_proj/value_proj/out_proj
    """
    k = pt_key
    k = re.sub(r'downsamplers\.\d+\.conv\.', 'downsample.', k)
    k = re.sub(r'upsamplers\.\d+\.conv\.', 'upsample.', k)
    k = k.replace('mid_block.resnets.0.', 'mid_blocks.0.')
    k = k.replace('mid_block.attentions.0.', 'mid_blocks.1.')
    k = k.replace('mid_block.resnets.1.', 'mid_blocks.2.')
    k = re.sub(r'\.to_q\.', '.query_proj.', k)
    k = re.sub(r'\.to_k\.', '.key_proj.', k)
    k = re.sub(r'\.to_v\.', '.value_proj.', k)
    k = re.sub(r'\.to_out\.\d+\.', '.out_proj.', k)
    return k


def _transform_conv_weight(pt_key: str, val_np: np.ndarray) -> np.ndarray:
    """
    Reshape Conv2d weights for MLX:
      - 1×1 Conv2d used as Linear (conv_shortcut, quant_conv, post_quant_conv):
        (out, in, 1, 1) → (out, in)
      - All other Conv2d: (out, in, kH, kW) → (out, kH, kW, in)
    """
    if val_np.ndim != 4 or "weight" not in pt_key:
        return val_np
    if "conv_shortcut" in pt_key or "quant_conv" in pt_key:
        return val_np[:, :, 0, 0]
    return val_np.transpose(0, 2, 3, 1)


def load_vae_weights(mlx_vae: Any, hf_model_id: str = "stabilityai/sd-vae-ft-mse") -> list[str]:
    """Load sd-vae-ft-mse weights from HuggingFace into an MLX VAEKL model."""
    from diffusers import AutoencoderKL
    pt_vae = AutoencoderKL.from_pretrained(hf_model_id, torch_dtype=None)
    skipped = []
    for pt_key, pt_val in pt_vae.state_dict().items():
        mlx_key = _remap_vae_key(pt_key)
        val_np = _transform_conv_weight(pt_key, _torch_to_np(pt_val))
        parts = mlx_key.split(".")
        try:
            _set_nested(mlx_vae, parts, mx.array(val_np))
        except (AttributeError, IndexError, TypeError) as e:
            skipped.append(f"{pt_key} → {mlx_key}: {e}")
    return skipped


# ── Whisper ──────────────────────────────────────────────────────────────────

def _remap_whisper_key(pt_key: str) -> str | None:
    """
    Remap Whisper checkpoint key to MLX AudioEncoderMLX attribute path.

    Checkpoint format: encoder.{blocks.N.attn.*|conv1|ln_post|positional_embedding}
    Our model: AudioEncoderMLX with {blocks[N].attn.*|conv1|ln_post|_pos_emb}

    decoder.* keys are skipped (only encoder is used for feature extraction).
    """
    if pt_key.startswith("decoder."):
        return None

    # Strip the encoder. prefix — our model IS the encoder
    if pt_key.startswith("encoder."):
        k = pt_key[len("encoder."):]
    else:
        k = pt_key

    # positional_embedding → _pos_emb (stored as plain array, not nn.Module param)
    if k == "positional_embedding":
        return "_pos_emb"

    # mlp.0.* → mlp1.* and mlp.2.* → mlp2.*
    # (PyTorch MLP: [Linear, GELU, Linear]; our model uses mlp1/mlp2 attributes)
    k = re.sub(r'\.mlp\.0\.', '.mlp1.', k)
    k = re.sub(r'\.mlp\.2\.', '.mlp2.', k)

    return k


def load_whisper_weights(mlx_whisper: Any, ckpt_path: str | Path) -> list[str]:
    """Load Whisper tiny weights (from LatentSync checkpoints) into MLX AudioEncoderMLX."""
    import torch
    raw = torch.load(str(ckpt_path), map_location="cpu", weights_only=True)
    state_dict = raw.get("model_state_dict", raw)

    skipped = []
    for pt_key, pt_val in state_dict.items():
        mlx_key = _remap_whisper_key(pt_key)
        if mlx_key is None:
            continue

        val_np = _torch_to_np(pt_val)

        # Conv1d weight: PyTorch (out, in, k) → MLX (out, k, in)
        if val_np.ndim == 3 and "conv" in pt_key and "weight" in pt_key:
            val_np = val_np.transpose(0, 2, 1)

        parts = mlx_key.split(".")
        try:
            _set_nested(mlx_whisper, parts, mx.array(val_np))
        except (AttributeError, IndexError, TypeError) as e:
            skipped.append(f"{pt_key} → {mlx_key}: {e}")

    return skipped


# ── 3D UNet ───────────────────────────────────────────────────────────────────

def _remap_unet_key(pt_key: str) -> str | None:
    """
    Remap a LatentSync UNet checkpoint key to the MLX UNet3DConditionMLX path.

    Key structural differences between the PyTorch checkpoint and our MLX model:
      - motion_modules.*: temporal attention — not implemented, skip
      - mid_block.resnets.{0,1} → mid_block.{resnet1,resnet2}
      - mid_block.attentions.0 → mid_block.attn
      - *.downsamplers.0.conv → *.downsample  (Conv2d stored directly, no wrapper)
      - *.upsamplers.0.conv  → *.upsample
      - *.to_out.0.*         → *.to_out.*     (Sequential[0] in PyTorch; direct in MLX)
      - *.ff.net.2.*         → *.ff.net.1.*   (Dropout at index 1 removed in MLX)
    """
    if "motion_modules" in pt_key:
        return None

    k = pt_key

    # mid_block structural renames
    k = k.replace("mid_block.resnets.0.", "mid_block.resnet1.")
    k = k.replace("mid_block.resnets.1.", "mid_block.resnet2.")
    k = k.replace("mid_block.attentions.0.", "mid_block.attn.")

    # Downsampler/upsampler wrappers
    k = re.sub(r'downsamplers\.0\.conv\.', 'downsample.', k)
    k = re.sub(r'upsamplers\.0\.conv\.', 'upsample.', k)

    # to_out: strip the Sequential index (no Dropout in MLX)
    k = re.sub(r'\.to_out\.0\.', '.to_out.', k)

    # FeedForward: Dropout was at index 1 in PyTorch Sequential, removed in MLX
    k = re.sub(r'\.ff\.net\.2\.', '.ff.net.1.', k)

    return k




def load_unet_weights(mlx_unet: Any, ckpt_path: str | Path) -> list[str]:
    """
    Load LatentSync UNet checkpoint into an MLX UNet3DConditionMLX model.

    Handles:
      - state_dict nested under 'state_dict' top-level key
      - key path remapping (motion_modules skipped, mid_block renamed, etc.)
      - Conv2d weight transposition to MLX channel-last layout
      - conv_shortcut (1×1 Conv2d in PyTorch → Linear in MLX): shape squeeze
    """
    import torch
    raw = torch.load(str(ckpt_path), map_location="cpu", weights_only=True)
    state_dict = raw.get("state_dict", raw)

    skipped = []
    for pt_key, pt_val in state_dict.items():
        mlx_key = _remap_unet_key(pt_key)
        if mlx_key is None:
            continue

        val_np = _transform_conv_weight(pt_key, _torch_to_np(pt_val))

        parts = mlx_key.split(".")
        try:
            _set_nested(mlx_unet, parts, mx.array(val_np))
        except (AttributeError, IndexError, TypeError) as e:
            skipped.append(f"{pt_key} → {mlx_key}: {e}")

    return skipped
