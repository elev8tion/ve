"""
LatentSync MLX inference pipeline.

Orchestrates VAE + Whisper + 3D UNet + DDIM scheduler to produce
lip-synced video from a raw video + audio input.

Drop-in replacement for LatentSync's lipsync_pipeline.py — same interface
expected by tools/latentsync.py but runs natively on Apple Silicon via MLX.
"""

from pathlib import Path
from typing import Optional
import subprocess
import tempfile

import mlx.core as mx
import mlx.nn as nn
import numpy as np

from .vae import VAEKL, build_vae
from .whisper import Audio2FeatureMLX
from .unet import UNet3DConditionMLX, build_unet
from .scheduler import DDIMSchedulerMLX
from .weights import load_vae_weights, load_unet_weights


# ── Video I/O helpers ─────────────────────────────────────────────────────────

def read_video_frames(video_path: str) -> tuple[np.ndarray, float]:
    """
    Read video into (N, H, W, 3) uint8 array and return (frames, fps).
    Uses cv2 for decoding.
    """
    import cv2
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frames = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cap.release()
    return np.stack(frames), fps


def write_video_frames(frames: np.ndarray, fps: float, out_path: str,
                       audio_path: Optional[str] = None) -> None:
    """Write (N, H, W, 3) uint8 frames to mp4, optionally muxing audio."""
    import cv2
    N, H, W, _ = frames.shape
    tmp_video = out_path if audio_path is None else out_path + ".noaudio.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(tmp_video, fourcc, fps, (W, H))
    for frame in frames:
        writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    writer.release()

    if audio_path is not None:
        import shutil
        ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
        subprocess.run([
            ffmpeg, "-y",
            "-i", tmp_video,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            out_path,
        ], check=True, capture_output=True)
        Path(tmp_video).unlink(missing_ok=True)


def frames_to_latents(frames_uint8: np.ndarray, vae: VAEKL) -> mx.array:
    """(N, H, W, 3) uint8 → (N, H/8, W/8, 4) latents."""
    frames_f = (frames_uint8.astype(np.float32) / 127.5) - 1.0
    return vae.encode_frames(mx.array(frames_f))


def latents_to_frames(latents: mx.array, vae: VAEKL) -> np.ndarray:
    """(N, H/8, W/8, 4) latents → (N, H, W, 3) uint8."""
    out = vae.decode_frames(latents)
    mx.eval(out)
    frames_f = np.array(out)
    frames_f = np.clip((frames_f + 1.0) * 127.5, 0, 255).astype(np.uint8)
    return frames_f


# ── Pipeline ──────────────────────────────────────────────────────────────────

class LipsyncPipelineMLX:
    """
    LatentSync inference pipeline running natively on Apple Silicon.

    Usage:
        pipe = LipsyncPipelineMLX.from_checkpoints(
            unet_ckpt  = "tools/LatentSync/checkpoints/unet/latentsync_unet.pt",
            whisper_ckpt = "tools/LatentSync/checkpoints/whisper/tiny.pt",
        )
        pipe(video_path, audio_path, output_path, num_inference_steps=20)
    """

    def __init__(
        self,
        vae: VAEKL,
        audio_encoder: Audio2FeatureMLX,
        unet: UNet3DConditionMLX,
        scheduler: DDIMSchedulerMLX,
    ):
        self.vae           = vae
        self.audio_encoder = audio_encoder
        self.unet          = unet
        self.scheduler     = scheduler
        # No projection: Whisper tiny (384) → UNet cross_attention_dim (384) directly

    @classmethod
    def from_checkpoints(
        cls,
        unet_ckpt: str,
        whisper_ckpt: str,
        vae_hf_id: str = "stabilityai/sd-vae-ft-mse",
    ) -> "LipsyncPipelineMLX":
        print("[LatentSync-MLX] Loading VAE...")
        vae = build_vae()
        skipped = load_vae_weights(vae, vae_hf_id)
        if skipped:
            print(f"  VAE: {len(skipped)} keys skipped")
        mx.eval(vae.parameters())

        print("[LatentSync-MLX] Loading Whisper audio encoder...")
        audio_enc = Audio2FeatureMLX.from_checkpoint(whisper_ckpt)

        print("[LatentSync-MLX] Loading 3D UNet...")
        # 13 = 4 noisy + 4 masked latents + 4 ref latents + 1 binary mask (stage2.yaml)
        unet = build_unet(in_channels=13)
        skipped = load_unet_weights(unet, unet_ckpt)
        if skipped:
            print(f"  UNet: {len(skipped)} keys skipped")
        mx.eval(unet.parameters())

        scheduler = DDIMSchedulerMLX(
            num_train_timesteps=1000,
            beta_start=0.00085,
            beta_end=0.012,
            beta_schedule="scaled_linear",
        )

        return cls(vae, audio_enc, unet, scheduler)  # no audio_proj — 384 == cross_attention_dim

    def __call__(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        num_inference_steps: int = 20,
        guidance_scale: float = 2.0,
        fps: Optional[float] = None,
    ) -> None:
        print("[LatentSync-MLX] Reading video frames...")
        frames_np, detected_fps = read_video_frames(video_path)
        video_fps = fps or detected_fps
        N = len(frames_np)
        print(f"  {N} frames @ {video_fps:.1f} fps")

        print("[LatentSync-MLX] Extracting audio features...")
        audio_feat = self.audio_encoder.audio2feat(audio_path)   # (T_ctx, 384)
        audio_chunks = self.audio_encoder.feature2chunks(audio_feat, fps=video_fps)
        # Pad or trim to match frame count
        while len(audio_chunks) < N:
            audio_chunks.append(audio_chunks[-1])
        audio_chunks = audio_chunks[:N]
        # Stack: (N, 50, 384) — directly usable as UNet cross_attention (dim=384)
        audio_seq = np.stack(audio_chunks, axis=0)  # (N, 50, 384)
        audio_mx  = mx.array(audio_seq.astype(np.float32))
        mx.eval(audio_mx)

        print("[LatentSync-MLX] Encoding video latents...")
        latents = frames_to_latents(frames_np, self.vae)  # (N, h, w, 4)
        mx.eval(latents)

        # Build 13-channel UNet conditioning input per stage2.yaml:
        #   ch 0-3:  noisy denoised latents (added during DDIM loop below)
        #   ch 4-7:  masked latents (lower-half face region zeroed out)
        #   ch 8-11: reference (full) latents
        #   ch 12:   binary mask (1 = masked region)
        h, w = latents.shape[1], latents.shape[2]
        mask = mx.zeros((len(latents), h, w, 1))
        mask = mask.at[:, h // 2:, :, :].set(1.0)
        masked_latents = latents * (1.0 - mask)          # zero out lower half
        # conditioning = [masked(4) | ref(4) | mask(1)] = 9 ch appended after noisy(4)
        conditioning = mx.concatenate([masked_latents, latents, mask], axis=-1)  # (N, h, w, 9)

        # Add batch dim: (1, N, h, w, 9)
        conditioning = conditioning[None]
        audio_mx     = audio_mx[None]  # (1, N, 50, 384)

        # Add noise and run DDIM — noisy is (1, N, h, w, 4)
        print(f"[LatentSync-MLX] DDIM denoising ({num_inference_steps} steps)...")
        self.scheduler.set_timesteps(num_inference_steps)
        noisy = mx.random.normal((1, N, h, w, 4))

        for step_idx, t in enumerate(self.scheduler.timesteps):
            t_tensor = mx.array([t])
            # 13-ch input: concat noisy(4) with conditioning(9) on channel axis
            unet_in = mx.concatenate([noisy, conditioning], axis=-1)
            noise_pred = self.unet(unet_in, t_tensor, audio_mx)
            noisy = self.scheduler.step(noise_pred, int(t), noisy, eta=0.0)
            mx.eval(noisy)
            if step_idx % 5 == 0:
                print(f"  step {step_idx + 1}/{num_inference_steps}")

        print("[LatentSync-MLX] Decoding output frames...")
        out_latents = noisy[0]  # (N, h, w, 4)
        out_frames  = latents_to_frames(out_latents, self.vae)  # (N, H, W, 3)

        print("[LatentSync-MLX] Writing output video...")
        write_video_frames(out_frames, video_fps, output_path, audio_path=audio_path)
        print(f"[LatentSync-MLX] Done → {output_path}")
