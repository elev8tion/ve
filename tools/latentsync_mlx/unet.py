"""
3D UNet for LatentSync MLX.

Extends Apple's mlx-examples SD UNet (2D) with:
  1. Frame dimension: inputs are (B, F, H, W, C) — frames treated as extended batch
  2. Audio cross-attention: in BasicTransformerBlock, attn2 cross-attends to
     Whisper audio embeddings (shape: B*F, T_audio, 384) instead of text encoder

Architecture matches LatentSync's UNet3DConditionModel config:
  block_out_channels = [320, 640, 1280, 1280]
  down_block_types   = [CrossAttn, CrossAttn, CrossAttn, Down]
  up_block_types     = [Up, CrossAttn, CrossAttn, CrossAttn]
  cross_attention_dim = 1280 (audio feature dim after projection)
  attention_head_dim  = 8
  layers_per_block    = 2
  add_audio_layer     = True (enables attn2 in every CrossAttn block)
"""

import math
from typing import List, Optional, Tuple

import mlx.core as mx
import mlx.nn as nn


# ── Timestep utilities ────────────────────────────────────────────────────────

def _sinusoidal_embed(timesteps: mx.array, dim: int,
                      flip_sin_to_cos: bool = True) -> mx.array:
    """Sinusoidal timestep embedding matching diffusers Timesteps."""
    half = dim // 2
    freqs = mx.exp(
        -math.log(10000) * mx.arange(half, dtype=mx.float32) / (half - 1)
    )
    # timesteps: (B,)  freqs: (half,)
    args = timesteps[:, None].astype(mx.float32) * freqs[None, :]
    if flip_sin_to_cos:
        emb = mx.concatenate([mx.cos(args), mx.sin(args)], axis=-1)
    else:
        emb = mx.concatenate([mx.sin(args), mx.cos(args)], axis=-1)
    return emb


class TimestepEmbedding(nn.Module):
    def __init__(self, in_channels: int, time_embed_dim: int):
        super().__init__()
        self.linear_1 = nn.Linear(in_channels, time_embed_dim)
        self.linear_2 = nn.Linear(time_embed_dim, time_embed_dim)

    def __call__(self, x):
        return self.linear_2(nn.silu(self.linear_1(x)))


# ── Core building blocks ──────────────────────────────────────────────────────

def upsample_nearest(x, scale: int = 2):
    B, H, W, C = x.shape
    x = mx.broadcast_to(x[:, :, None, :, None, :], (B, H, scale, W, scale, C))
    return x.reshape(B, H * scale, W * scale, C)


class ResnetBlock3D(nn.Module):
    """ResNet block that handles a time embedding; operates per-frame (B*F, H, W, C)."""

    def __init__(self, in_channels: int, out_channels: int,
                 temb_channels: int, groups: int = 32):
        super().__init__()
        self.norm1 = nn.GroupNorm(groups, in_channels, pytorch_compatible=True)
        self.conv1 = nn.Conv2d(in_channels, out_channels, 3, padding=1)
        self.time_emb_proj = nn.Linear(temb_channels, out_channels)
        self.norm2 = nn.GroupNorm(groups, out_channels, pytorch_compatible=True)
        self.conv2 = nn.Conv2d(out_channels, out_channels, 3, padding=1)
        if in_channels != out_channels:
            self.conv_shortcut = nn.Linear(in_channels, out_channels)

    def __call__(self, x: mx.array, temb: mx.array) -> mx.array:
        # x: (BF, H, W, C)   temb: (BF, temb_channels)
        y = nn.silu(self.norm1(x))
        y = self.conv1(y)
        y = y + self.time_emb_proj(nn.silu(temb))[:, None, None, :]
        y = nn.silu(self.norm2(y))
        y = self.conv2(y)
        if "conv_shortcut" in self:
            x = self.conv_shortcut(x)
        return x + y


class Attention(nn.Module):
    """Single scaled dot-product attention (self or cross)."""

    def __init__(self, query_dim: int, context_dim: Optional[int] = None,
                 heads: int = 8, dim_head: int = 64):
        super().__init__()
        inner_dim = heads * dim_head
        context_dim = context_dim or query_dim
        self.heads = heads
        self.scale = dim_head ** -0.5
        self.to_q = nn.Linear(query_dim, inner_dim, bias=False)
        self.to_k = nn.Linear(context_dim, inner_dim, bias=False)
        self.to_v = nn.Linear(context_dim, inner_dim, bias=False)
        self.to_out = nn.Linear(inner_dim, query_dim)

    def __call__(self, x: mx.array, context: Optional[mx.array] = None) -> mx.array:
        B, T, _ = x.shape
        nh, hd = self.heads, x.shape[-1] // self.heads
        src = context if context is not None else x

        q = self.to_q(x)
        k = self.to_k(src)
        v = self.to_v(src)

        # (B, T, nh*hd) → (B, nh, T, hd)
        def split_heads(t):
            B, S, D = t.shape
            return t.reshape(B, S, self.heads, D // self.heads).transpose(0, 2, 1, 3)

        q, k, v = split_heads(q), split_heads(k), split_heads(v)
        attn = mx.softmax(q @ k.transpose(0, 1, 3, 2) * self.scale, axis=-1)
        out = (attn @ v).transpose(0, 2, 1, 3).reshape(B, T, -1)
        return self.to_out(out)


class GEGLU(nn.Module):
    def __init__(self, dim_in: int, dim_out: int):
        super().__init__()
        self.proj = nn.Linear(dim_in, dim_out * 2)

    def __call__(self, x):
        x, gate = self.proj(x).split(2, axis=-1)
        return x * nn.gelu(gate)


class FeedForward(nn.Module):
    def __init__(self, dim: int, mult: int = 4):
        super().__init__()
        self.net = [GEGLU(dim, dim * mult), nn.Linear(dim * mult, dim)]

    def __call__(self, x):
        for layer in self.net:
            x = layer(x)
        return x


class BasicTransformerBlock(nn.Module):
    """
    Spatial + audio cross-attention transformer block.

    attn1: self-attention over spatial tokens
    attn2: cross-attention to audio features (when add_audio_layer=True)
    ff:    GEGLU feed-forward
    """

    def __init__(self, dim: int, num_heads: int, dim_head: int,
                 cross_attention_dim: int, add_audio_layer: bool):
        super().__init__()
        self.norm1 = nn.LayerNorm(dim)
        self.attn1 = Attention(dim, heads=num_heads, dim_head=dim_head)

        self.add_audio_layer = add_audio_layer
        if add_audio_layer:
            self.norm2 = nn.LayerNorm(dim)
            self.attn2 = Attention(dim, context_dim=cross_attention_dim,
                                   heads=num_heads, dim_head=dim_head)

        self.norm3 = nn.LayerNorm(dim)
        self.ff = FeedForward(dim)

    def __call__(self, x: mx.array,
                 audio_emb: Optional[mx.array] = None) -> mx.array:
        x = self.attn1(self.norm1(x)) + x
        if self.add_audio_layer and audio_emb is not None:
            x = self.attn2(self.norm2(x), context=audio_emb) + x
        x = self.ff(self.norm3(x)) + x
        return x


class Transformer3D(nn.Module):
    """
    Spatial transformer that operates on 4D (B*F, H, W, C) tensors.

    Internally flattens spatial dims to sequence, applies transformer blocks,
    then unflattens. Identical to Transformer2D in Apple's UNet but with
    the audio cross-attention added.
    """

    def __init__(self, in_channels: int, num_heads: int, dim_head: int,
                 num_layers: int, cross_attention_dim: int,
                 norm_groups: int, add_audio_layer: bool):
        super().__init__()
        model_dim = num_heads * dim_head
        self.norm = nn.GroupNorm(norm_groups, in_channels, pytorch_compatible=True)
        self.proj_in  = nn.Conv2d(in_channels, model_dim, 1)
        self.transformer_blocks = [
            BasicTransformerBlock(model_dim, num_heads, dim_head,
                                  cross_attention_dim, add_audio_layer)
            for _ in range(num_layers)
        ]
        self.proj_out = nn.Conv2d(model_dim, in_channels, 1)

    def __call__(self, x: mx.array,
                 audio_emb: Optional[mx.array] = None) -> mx.array:
        # x: (BF, H, W, C)   audio_emb: (BF, T_audio, audio_dim) or None
        B, H, W, C = x.shape
        residual = x
        x = self.norm(x)
        x = self.proj_in(x)               # (BF, H, W, model_dim)
        x = x.reshape(B, H * W, -1)       # (BF, H*W, model_dim)
        for block in self.transformer_blocks:
            x = block(x, audio_emb=audio_emb)
        x = x.reshape(B, H, W, -1)
        x = self.proj_out(x)
        return x + residual


# ── Down / Up blocks ──────────────────────────────────────────────────────────

class CrossAttnDownBlock3D(nn.Module):
    def __init__(self, in_ch: int, out_ch: int, temb_ch: int,
                 num_layers: int, num_heads: int, dim_head: int,
                 cross_attention_dim: int, norm_groups: int,
                 add_downsample: bool, add_audio_layer: bool):
        super().__init__()
        self.resnets = [
            ResnetBlock3D(in_ch if i == 0 else out_ch, out_ch, temb_ch, norm_groups)
            for i in range(num_layers)
        ]
        self.attentions = [
            Transformer3D(out_ch, num_heads, dim_head, 1, cross_attention_dim,
                          norm_groups, add_audio_layer)
            for _ in range(num_layers)
        ]
        if add_downsample:
            self.downsample = nn.Conv2d(out_ch, out_ch, 3, stride=2, padding=1)

    def __call__(self, x, temb, audio_emb=None):
        outs = []
        for resnet, attn in zip(self.resnets, self.attentions):
            x = resnet(x, temb)
            x = attn(x, audio_emb=audio_emb)
            outs.append(x)
        if "downsample" in self:
            x = self.downsample(x)
            outs.append(x)
        return x, outs


class DownBlock3D(nn.Module):
    def __init__(self, in_ch: int, out_ch: int, temb_ch: int,
                 num_layers: int, norm_groups: int, add_downsample: bool):
        super().__init__()
        self.resnets = [
            ResnetBlock3D(in_ch if i == 0 else out_ch, out_ch, temb_ch, norm_groups)
            for i in range(num_layers)
        ]
        if add_downsample:
            self.downsample = nn.Conv2d(out_ch, out_ch, 3, stride=2, padding=1)

    def __call__(self, x, temb, audio_emb=None):
        outs = []
        for resnet in self.resnets:
            x = resnet(x, temb)
            outs.append(x)
        if "downsample" in self:
            x = self.downsample(x)
            outs.append(x)
        return x, outs


class CrossAttnUpBlock3D(nn.Module):
    def __init__(self, in_ch: int, out_ch: int, prev_ch: int, temb_ch: int,
                 num_layers: int, num_heads: int, dim_head: int,
                 cross_attention_dim: int, norm_groups: int,
                 add_upsample: bool, add_audio_layer: bool):
        super().__init__()
        self.resnets = [
            ResnetBlock3D(
                (in_ch if i == num_layers - 1 else out_ch) + (prev_ch if i == 0 else out_ch),
                out_ch, temb_ch, norm_groups,
            )
            for i in range(num_layers)
        ]
        self.attentions = [
            Transformer3D(out_ch, num_heads, dim_head, 1, cross_attention_dim,
                          norm_groups, add_audio_layer)
            for _ in range(num_layers)
        ]
        if add_upsample:
            self.upsample = nn.Conv2d(out_ch, out_ch, 3, padding=1)

    def __call__(self, x, temb, residuals: list, audio_emb=None):
        for resnet, attn in zip(self.resnets, self.attentions):
            res = residuals.pop()
            x = mx.concatenate([x, res], axis=-1)
            x = resnet(x, temb)
            x = attn(x, audio_emb=audio_emb)
        if "upsample" in self:
            x = self.upsample(upsample_nearest(x))
        return x


class UpBlock3D(nn.Module):
    def __init__(self, in_ch: int, out_ch: int, prev_ch: int, temb_ch: int,
                 num_layers: int, norm_groups: int, add_upsample: bool):
        super().__init__()
        self.resnets = [
            ResnetBlock3D(
                (in_ch if i == num_layers - 1 else out_ch) + (prev_ch if i == 0 else out_ch),
                out_ch, temb_ch, norm_groups,
            )
            for i in range(num_layers)
        ]
        if add_upsample:
            self.upsample = nn.Conv2d(out_ch, out_ch, 3, padding=1)

    def __call__(self, x, temb, residuals: list, audio_emb=None):
        for resnet in self.resnets:
            res = residuals.pop()
            x = mx.concatenate([x, res], axis=-1)
            x = resnet(x, temb)
        if "upsample" in self:
            x = self.upsample(upsample_nearest(x))
        return x


class MidBlock3D(nn.Module):
    def __init__(self, channels: int, temb_ch: int, num_heads: int, dim_head: int,
                 cross_attention_dim: int, norm_groups: int, add_audio_layer: bool):
        super().__init__()
        self.resnet1 = ResnetBlock3D(channels, channels, temb_ch, norm_groups)
        self.attn    = Transformer3D(channels, num_heads, dim_head, 1,
                                     cross_attention_dim, norm_groups, add_audio_layer)
        self.resnet2 = ResnetBlock3D(channels, channels, temb_ch, norm_groups)

    def __call__(self, x, temb, audio_emb=None):
        x = self.resnet1(x, temb)
        x = self.attn(x, audio_emb=audio_emb)
        x = self.resnet2(x, temb)
        return x


# ── Main model ────────────────────────────────────────────────────────────────

class UNet3DConditionMLX(nn.Module):
    """
    LatentSync UNet in MLX.

    Input:  latents (B, F, H, W, C) + timestep (B,) + audio_emb (B, F, T_a, D)
    Output: noise prediction (B, F, H, W, C)

    Frames are folded into the batch dimension before spatial ops and unfolded
    at the end — this avoids any 5D convolution ops (not needed given LatentSync's
    architecture does not use motion modules).
    """

    # LatentSync stage2.yaml config
    BLOCK_OUT_CHANNELS    = (320, 640, 1280, 1280)
    LAYERS_PER_BLOCK      = 2
    ATTENTION_HEAD_DIM    = 8
    CROSS_ATTENTION_DIM   = 384   # Whisper tiny output dim — no projection layer
    NORM_NUM_GROUPS       = 32
    IN_CHANNELS           = 4    # latent channels (8 masked + 4 reference, see lipsync_pipeline)
    OUT_CHANNELS          = 4

    def __init__(self, in_channels: int = IN_CHANNELS,
                 add_audio_layer: bool = True):
        super().__init__()
        ch = self.BLOCK_OUT_CHANNELS
        temb_ch = ch[0] * 4
        lpb = self.LAYERS_PER_BLOCK
        hd = self.ATTENTION_HEAD_DIM
        ca_dim = self.CROSS_ATTENTION_DIM
        g = self.NORM_NUM_GROUPS

        self.conv_in = nn.Conv2d(in_channels, ch[0], 3, padding=1)

        self.time_proj = None  # set via sinusoidal_embed helper
        self.time_embedding = TimestepEmbedding(ch[0], temb_ch)

        # Down blocks: [CrossAttn, CrossAttn, CrossAttn, Down]
        self.down_blocks = [
            CrossAttnDownBlock3D(ch[0], ch[0], temb_ch, lpb, ch[0]//hd, hd, ca_dim, g,
                                 add_downsample=True, add_audio_layer=add_audio_layer),
            CrossAttnDownBlock3D(ch[0], ch[1], temb_ch, lpb, ch[1]//hd, hd, ca_dim, g,
                                 add_downsample=True, add_audio_layer=add_audio_layer),
            CrossAttnDownBlock3D(ch[1], ch[2], temb_ch, lpb, ch[2]//hd, hd, ca_dim, g,
                                 add_downsample=True, add_audio_layer=add_audio_layer),
            DownBlock3D(ch[2], ch[3], temb_ch, lpb, g, add_downsample=False),
        ]

        self.mid_block = MidBlock3D(ch[3], temb_ch, ch[3]//hd, hd, ca_dim, g,
                                    add_audio_layer=add_audio_layer)

        # Up blocks: [Up, CrossAttn, CrossAttn, CrossAttn]
        # in_ch = the skip-connection channel width for the LAST skip pop in each block,
        # which matches reversed_block_out_channels[i+1] from the PyTorch convention.
        # rch = reversed channels: [1280, 1280, 640, 320]
        rch = list(reversed(ch))   # [1280, 1280, 640, 320]
        self.up_blocks = [
            # i=0: prev=rch[0]=1280, out=rch[0]=1280, in=rch[1]=1280  (all Down3 outputs)
            UpBlock3D(rch[1], rch[0], rch[0], temb_ch, lpb + 1, g, add_upsample=True),
            # i=1: prev=1280, out=rch[1]=1280, in=rch[2]=640           (last skip from Down1 downsample)
            CrossAttnUpBlock3D(rch[2], rch[1], rch[0], temb_ch, lpb + 1, rch[1]//hd, hd,
                               ca_dim, g, add_upsample=True, add_audio_layer=add_audio_layer),
            # i=2: prev=1280, out=rch[2]=640, in=rch[3]=320            (last skip from Down0 downsample)
            CrossAttnUpBlock3D(rch[3], rch[2], rch[1], temb_ch, lpb + 1, rch[2]//hd, hd,
                               ca_dim, g, add_upsample=True, add_audio_layer=add_audio_layer),
            # i=3: prev=640, out=rch[3]=320, in=rch[3]=320             (conv_in skip at full res)
            CrossAttnUpBlock3D(rch[3], rch[3], rch[2], temb_ch, lpb + 1, rch[3]//hd, hd,
                               ca_dim, g, add_upsample=False, add_audio_layer=add_audio_layer),
        ]

        self.conv_norm_out = nn.GroupNorm(g, ch[0], pytorch_compatible=True)
        self.conv_out = nn.Conv2d(ch[0], self.OUT_CHANNELS, 3, padding=1)

    def __call__(
        self,
        sample: mx.array,        # (B, F, H, W, C)
        timestep: mx.array,      # (B,) integer timesteps
        audio_emb: mx.array,     # (B, F, T_audio, audio_dim)
    ) -> mx.array:
        B, F, H, W, C = sample.shape

        # Fold frames into batch
        x = sample.reshape(B * F, H, W, C)

        # Timestep embedding — broadcast across frames
        t_emb = _sinusoidal_embed(timestep, self.BLOCK_OUT_CHANNELS[0])
        t_emb = self.time_embedding(t_emb)          # (B, temb_ch)
        t_emb = mx.repeat(t_emb, F, axis=0)         # (B*F, temb_ch)

        # Audio embedding — fold frames into batch
        # audio_emb: (B, F, T_audio, D) → (B*F, T_audio, D)
        a_emb = audio_emb.reshape(B * F, audio_emb.shape[2], audio_emb.shape[3])

        # Initial conv
        x = self.conv_in(x)

        # Down
        residuals = [x]
        for block in self.down_blocks:
            x, res = block(x, t_emb, audio_emb=a_emb)
            residuals.extend(res)

        # Mid
        x = self.mid_block(x, t_emb, audio_emb=a_emb)

        # Up
        for block in self.up_blocks:
            res_slice = residuals[-len(block.resnets):]
            residuals  = residuals[: -len(block.resnets)]
            x = block(x, t_emb, residuals=list(res_slice), audio_emb=a_emb)

        # Post-process
        x = self.conv_out(nn.silu(self.conv_norm_out(x)))

        # Unfold frames
        return x.reshape(B, F, H, W, self.OUT_CHANNELS)


def build_unet(in_channels: int = UNet3DConditionMLX.IN_CHANNELS,
               add_audio_layer: bool = True) -> UNet3DConditionMLX:
    return UNet3DConditionMLX(in_channels=in_channels, add_audio_layer=add_audio_layer)
