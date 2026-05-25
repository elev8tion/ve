"""
VAE for LatentSync MLX — adapted from Apple's mlx-examples/stable_diffusion.

Uses the stabilityai/sd-vae-ft-mse checkpoint (same as LatentSync's PyTorch path).
Encode/decode operate on channel-last (B, H, W, C) tensors — MLX's native layout.

Key differences from Apple's reference:
- Factory function `load_vae()` handles weight mapping from PyTorch → MLX
- `encode_frames` / `decode_frames` batch over the temporal dimension
"""

import math
from typing import List

import mlx.core as mx
import mlx.nn as nn


# ── Building blocks (from Apple's mlx-examples/stable_diffusion) ─────────────

def upsample_nearest(x, scale: int = 2):
    B, H, W, C = x.shape
    x = mx.broadcast_to(x[:, :, None, :, None, :], (B, H, scale, W, scale, C))
    return x.reshape(B, H * scale, W * scale, C)


class VAEAttention(nn.Module):
    def __init__(self, dims: int, norm_groups: int = 32):
        super().__init__()
        self.group_norm = nn.GroupNorm(norm_groups, dims, pytorch_compatible=True)
        self.query_proj = nn.Linear(dims, dims)
        self.key_proj   = nn.Linear(dims, dims)
        self.value_proj = nn.Linear(dims, dims)
        self.out_proj   = nn.Linear(dims, dims)

    def __call__(self, x):
        B, H, W, C = x.shape
        y = self.group_norm(x)
        queries = self.query_proj(y).reshape(B, H * W, C)
        keys    = self.key_proj(y).reshape(B, H * W, C)
        values  = self.value_proj(y).reshape(B, H * W, C)
        scale = 1 / math.sqrt(queries.shape[-1])
        scores = (queries * scale) @ keys.transpose(0, 2, 1)
        attn = mx.softmax(scores, axis=-1)
        y = (attn @ values).reshape(B, H, W, C)
        return x + self.out_proj(y)


class ResnetBlock2D(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, groups: int = 32):
        super().__init__()
        self.norm1 = nn.GroupNorm(groups, in_channels, pytorch_compatible=True)
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=1, padding=1)
        self.norm2 = nn.GroupNorm(groups, out_channels, pytorch_compatible=True)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)
        if in_channels != out_channels:
            self.conv_shortcut = nn.Linear(in_channels, out_channels)

    def __call__(self, x):
        y = nn.silu(self.norm1(x))
        y = self.conv1(y)
        y = nn.silu(self.norm2(y))
        y = self.conv2(y)
        if "conv_shortcut" in self:
            x = self.conv_shortcut(x)
        return x + y


class EncoderDecoderBlock2D(nn.Module):
    def __init__(self, in_ch: int, out_ch: int, num_layers: int, groups: int,
                 add_downsample: bool, add_upsample: bool):
        super().__init__()
        self.resnets = [
            ResnetBlock2D(in_ch if i == 0 else out_ch, out_ch, groups)
            for i in range(num_layers)
        ]
        if add_downsample:
            self.downsample = nn.Conv2d(out_ch, out_ch, kernel_size=3, stride=2, padding=0)
        if add_upsample:
            self.upsample = nn.Conv2d(out_ch, out_ch, kernel_size=3, stride=1, padding=1)

    def __call__(self, x):
        for r in self.resnets:
            x = r(x)
        if "downsample" in self:
            x = mx.pad(x, [(0, 0), (0, 1), (0, 1), (0, 0)])
            x = self.downsample(x)
        if "upsample" in self:
            x = self.upsample(upsample_nearest(x))
        return x


class Encoder(nn.Module):
    def __init__(self, in_channels: int, out_channels: int,
                 block_out_channels: List[int], layers_per_block: int, groups: int):
        super().__init__()
        self.conv_in = nn.Conv2d(in_channels, block_out_channels[0], kernel_size=3, padding=1)
        channels = [block_out_channels[0]] + list(block_out_channels)
        self.down_blocks = [
            EncoderDecoderBlock2D(ic, oc, layers_per_block, groups,
                                  add_downsample=(i < len(block_out_channels) - 1),
                                  add_upsample=False)
            for i, (ic, oc) in enumerate(zip(channels, channels[1:]))
        ]
        self.mid_blocks = [
            ResnetBlock2D(block_out_channels[-1], block_out_channels[-1], groups),
            VAEAttention(block_out_channels[-1], groups),
            ResnetBlock2D(block_out_channels[-1], block_out_channels[-1], groups),
        ]
        self.conv_norm_out = nn.GroupNorm(groups, block_out_channels[-1], pytorch_compatible=True)
        self.conv_out = nn.Conv2d(block_out_channels[-1], out_channels, 3, padding=1)

    def __call__(self, x):
        x = self.conv_in(x)
        for b in self.down_blocks:
            x = b(x)
        for m in self.mid_blocks:
            x = m(x)
        return self.conv_out(nn.silu(self.conv_norm_out(x)))


class Decoder(nn.Module):
    def __init__(self, in_channels: int, out_channels: int,
                 block_out_channels: List[int], layers_per_block: int, groups: int):
        super().__init__()
        self.conv_in = nn.Conv2d(in_channels, block_out_channels[-1], kernel_size=3, padding=1)
        self.mid_blocks = [
            ResnetBlock2D(block_out_channels[-1], block_out_channels[-1], groups),
            VAEAttention(block_out_channels[-1], groups),
            ResnetBlock2D(block_out_channels[-1], block_out_channels[-1], groups),
        ]
        channels = list(reversed(block_out_channels))
        channels = [channels[0]] + channels
        self.up_blocks = [
            EncoderDecoderBlock2D(ic, oc, layers_per_block, groups,
                                  add_downsample=False,
                                  add_upsample=(i < len(block_out_channels) - 1))
            for i, (ic, oc) in enumerate(zip(channels, channels[1:]))
        ]
        self.conv_norm_out = nn.GroupNorm(groups, block_out_channels[0], pytorch_compatible=True)
        self.conv_out = nn.Conv2d(block_out_channels[0], out_channels, 3, padding=1)

    def __call__(self, x):
        x = self.conv_in(x)
        for m in self.mid_blocks:
            x = m(x)
        for b in self.up_blocks:
            x = b(x)
        return self.conv_out(nn.silu(self.conv_norm_out(x)))


class VAEKL(nn.Module):
    """
    KL-regularized autoencoder (sd-vae-ft-mse config).

    block_out_channels = [128, 256, 512, 512]
    latent_channels    = 4
    scaling_factor     = 0.18215
    """

    SCALING_FACTOR = 0.18215

    def __init__(
        self,
        in_channels: int = 3,
        out_channels: int = 3,
        block_out_channels: List[int] = (128, 256, 512, 512),
        latent_channels: int = 4,
        layers_per_block: int = 2,
        norm_num_groups: int = 32,
    ):
        super().__init__()
        self.encoder = Encoder(
            in_channels, latent_channels * 2,
            list(block_out_channels), layers_per_block, norm_num_groups,
        )
        self.decoder = Decoder(
            latent_channels, out_channels,
            list(block_out_channels), layers_per_block + 1, norm_num_groups,
        )
        # 1×1 conv → Linear equivalent (shape mapping handled in weights.py)
        self.quant_conv      = nn.Linear(latent_channels * 2, latent_channels * 2)
        self.post_quant_conv = nn.Linear(latent_channels, latent_channels)

    def encode(self, x: mx.array) -> mx.array:
        """x: (B, H, W, 3) in [-1, 1] → latents (B, H/8, W/8, 4)"""
        h = self.encoder(x)
        h = self.quant_conv(h)
        mean, _ = h.split(2, axis=-1)  # discard logvar at inference time
        return mean * self.SCALING_FACTOR

    def decode(self, z: mx.array) -> mx.array:
        """z: (B, H/8, W/8, 4) → frames (B, H, W, 3) in [-1, 1]"""
        z = z / self.SCALING_FACTOR
        return self.decoder(self.post_quant_conv(z))

    def encode_frames(self, frames: mx.array) -> mx.array:
        """frames: (F, H, W, 3) → latents (F, H/8, W/8, 4)"""
        return self.encode(frames)

    def decode_frames(self, latents: mx.array) -> mx.array:
        """latents: (F, H/8, W/8, 4) → frames (F, H, W, 3)"""
        return self.decode(latents)


def build_vae() -> VAEKL:
    """Construct a VAEKL with sd-vae-ft-mse architecture."""
    return VAEKL(
        in_channels=3,
        out_channels=3,
        block_out_channels=[128, 256, 512, 512],
        latent_channels=4,
        layers_per_block=2,
        norm_num_groups=32,
    )
