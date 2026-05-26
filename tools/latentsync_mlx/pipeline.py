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
from mlx.utils import tree_map


def _cast_to_float16(model: nn.Module) -> None:
    """Cast all float32 parameters in-place to float16 for 2-3× faster inference."""
    new_params = tree_map(
        lambda x: x.astype(mx.float16) if isinstance(x, mx.array) and x.dtype == mx.float32 else x,
        model.parameters(),
    )
    model.update(new_params)
    mx.eval(model.parameters())

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


def frames_to_latents(frames_uint8: np.ndarray, vae: VAEKL,
                       batch: int = 16) -> mx.array:
    """(N, H, W, 3) uint8 → (N, H/8, W/8, 4) latents, processed in batches."""
    frames_f = (frames_uint8.astype(np.float32) / 127.5) - 1.0
    chunks = []
    for i in range(0, len(frames_f), batch):
        z = vae.encode_frames(mx.array(frames_f[i:i + batch]))
        mx.eval(z)
        chunks.append(z)
    return mx.concatenate(chunks, axis=0)


def latents_to_frames(latents: mx.array, vae: VAEKL,
                       batch: int = 16) -> np.ndarray:
    """(N, H/8, W/8, 4) latents → (N, H, W, 3) uint8, processed in batches."""
    N = latents.shape[0]
    out_chunks = []
    for i in range(0, N, batch):
        chunk = vae.decode_frames(latents[i:i + batch])
        mx.eval(chunk)
        out_chunks.append(np.array(chunk))
    frames_f = np.concatenate(out_chunks, axis=0)
    return np.clip((frames_f + 1.0) * 127.5, 0, 255).astype(np.uint8)


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
        # Compile the UNet forward pass — MLX traces+caches the graph for fixed shapes
        self._unet_step    = mx.compile(self._run_unet_step)

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
        _cast_to_float16(vae)
        print("  VAE → float16")

        print("[LatentSync-MLX] Loading Whisper audio encoder...")
        audio_enc = Audio2FeatureMLX.from_checkpoint(whisper_ckpt)

        print("[LatentSync-MLX] Loading 3D UNet...")
        # 13 = 4 noisy + 4 masked latents + 4 ref latents + 1 binary mask (stage2.yaml)
        unet = build_unet(in_channels=13)
        skipped = load_unet_weights(unet, unet_ckpt)
        if skipped:
            print(f"  UNet: {len(skipped)} keys skipped")
        mx.eval(unet.parameters())
        _cast_to_float16(unet)
        print("  UNet → float16")

        scheduler = DDIMSchedulerMLX(
            num_train_timesteps=1000,
            beta_start=0.00085,
            beta_end=0.012,
            beta_schedule="scaled_linear",
        )

        return cls(vae, audio_enc, unet, scheduler)  # no audio_proj — 384 == cross_attention_dim

    def _run_unet_step(self, noisy: mx.array, t: mx.array,
                       cond: mx.array, audio: mx.array) -> mx.array:
        """Pure function wrapping UNet forward — compiled by mx.compile()."""
        return self.unet(mx.concatenate([noisy, cond], axis=-1), t, audio)

    def __call__(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        num_inference_steps: int = 20,
        guidance_scale: float = 2.0,
        fps: Optional[float] = None,
        chunk_frames: int = 16,
    ) -> None:
        print("[LatentSync-MLX] Reading video frames...")
        frames_np, detected_fps = read_video_frames(video_path)
        video_fps = fps or detected_fps
        N = len(frames_np)
        print(f"  {N} frames @ {video_fps:.1f} fps")

        print("[LatentSync-MLX] Extracting audio features...")
        audio_feat   = self.audio_encoder.audio2feat(audio_path)
        audio_chunks = self.audio_encoder.feature2chunks(audio_feat, fps=video_fps)
        while len(audio_chunks) < N:
            audio_chunks.append(audio_chunks[-1])
        audio_chunks = audio_chunks[:N]
        audio_seq = np.stack(audio_chunks, axis=0).astype(np.float32)  # (N, 50, 384)

        print("[LatentSync-MLX] Encoding video latents...")
        latents = frames_to_latents(frames_np, self.vae)  # (N, h, w, 4)
        mx.eval(latents)
        h, w = latents.shape[1], latents.shape[2]

        # Build per-frame mask + conditioning (9 ch: masked(4)|ref(4)|mask(1))
        mask_np                   = np.zeros((N, h, w, 1), dtype=np.float32)
        mask_np[:, h // 2:, :, :] = 1.0
        mask            = mx.array(mask_np)
        masked_latents  = latents * (1.0 - mask)
        conditioning    = mx.concatenate([masked_latents, latents, mask], axis=-1)  # (N,h,w,9)
        mx.eval(conditioning)

        # Process in chunks of `chunk_frames` (= 16, matching stage2.yaml num_frames)
        print(f"[LatentSync-MLX] DDIM denoising — {N} frames in chunks of {chunk_frames} "
              f"({num_inference_steps} steps each)...")
        self.scheduler.set_timesteps(num_inference_steps)

        out_latents_list = []
        n_chunks = (N + chunk_frames - 1) // chunk_frames

        for ci in range(n_chunks):
            s, e = ci * chunk_frames, min((ci + 1) * chunk_frames, N)
            F = e - s
            print(f"  chunk {ci+1}/{n_chunks}  frames {s}-{e-1}")

            # Cast conditioning + audio to float16 to match model weights
            cond_c  = conditioning[s:e][None].astype(mx.float16)  # (1,F,h,w,9)
            audio_c = mx.array(audio_seq[s:e])[None].astype(mx.float16)  # (1,F,50,384)
            noisy   = mx.random.normal((1, F, h, w, 4)).astype(mx.float16)
            mx.eval(cond_c, audio_c, noisy)

            for t in self.scheduler.timesteps:
                t_tensor   = mx.array([int(t)])
                noise_pred = self._unet_step(noisy, t_tensor, cond_c, audio_c)
                # Cast back to float32 for scheduler (pure math)
                noisy = self.scheduler.step(
                    noise_pred.astype(mx.float32), int(t),
                    noisy.astype(mx.float32), eta=0.0,
                ).astype(mx.float16)
                mx.eval(noisy)

            out_latents_list.append(noisy[0].astype(mx.float32))  # (F, h, w, 4)

        out_latents = mx.concatenate(out_latents_list, axis=0)  # (N, h, w, 4)

        print("[LatentSync-MLX] Decoding output frames...")
        out_frames = latents_to_frames(out_latents, self.vae)  # (N, H, W, 3)

        print("[LatentSync-MLX] Writing output video...")
        write_video_frames(out_frames, video_fps, output_path, audio_path=audio_path)
        print(f"[LatentSync-MLX] Done → {output_path}")
