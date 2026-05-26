"""
Whisper audio encoder for LatentSync MLX.

Wraps Apple's mlx-examples AudioEncoder and adds the LatentSync-specific
`Audio2FeatureMLX` interface: audio2feat() + feature2chunks().

The Whisper tiny model (checkpoints/whisper/tiny.pt) produces embeddings of
shape (T_ctx, 384) from an 80-mel spectrogram. LatentSync chunks these into
per-frame windows of 16 tokens: (num_frames, 16, 384) → cross-attention keys.
"""

import math
from pathlib import Path
from typing import List

import mlx.core as mx
import mlx.nn as nn
import numpy as np


# ── Whisper tiny constants ────────────────────────────────────────────────────

N_MELS     = 80
N_CTX      = 1500   # encoder context length (30 sec @ 50 Hz)
N_STATE    = 384    # tiny hidden dim
N_HEAD     = 6      # tiny attention heads
N_LAYER    = 4      # tiny encoder layers
# LatentSync audio_feat_length=[2,2]: window of 10 Whisper tokens, each (5, 384)
# → per-frame chunk = (50, 384). Matches stage2.yaml cross_attention_dim=384.
AUDIO_FEAT_LENGTH = [2, 2]   # left/right frames around center
TOKENS_PER_FEAT   = 2        # Whisper runs at 50 Hz; 25-fps video → 2 tokens/frame-step
CHUNK_SIZE        = (AUDIO_FEAT_LENGTH[0] + AUDIO_FEAT_LENGTH[1] + 1) * TOKENS_PER_FEAT  # = 10

HOP_LENGTH = 160    # for mel spectrogram
SAMPLE_RATE = 16000


# ── Sinusoidal positional encoding ────────────────────────────────────────────

def _sinusoids(length: int, channels: int, max_timescale: int = 10000) -> mx.array:
    assert channels % 2 == 0
    log_inc = math.log(max_timescale) / (channels // 2 - 1)
    inv_ts = mx.exp(-log_inc * mx.arange(channels // 2))
    t = mx.arange(length)[:, None] * inv_ts[None, :]
    return mx.concatenate([mx.sin(t), mx.cos(t)], axis=1)


# ── Model layers ──────────────────────────────────────────────────────────────

class _MHA(nn.Module):
    def __init__(self, n_state: int, n_head: int):
        super().__init__()
        self.n_head = n_head
        self.query  = nn.Linear(n_state, n_state)
        self.key    = nn.Linear(n_state, n_state, bias=False)
        self.value  = nn.Linear(n_state, n_state)
        self.out    = nn.Linear(n_state, n_state)

    def __call__(self, x, xa=None, mask=None):
        q = self.query(x)
        src = xa if xa is not None else x
        k = self.key(src)
        v = self.value(src)

        B, T, C = q.shape
        nh = self.n_head
        hd = C // nh
        scale = hd ** -0.25

        q = (q.reshape(B, T, nh, hd).transpose(0, 2, 1, 3)) * scale
        k = (k.reshape(B, -1, nh, hd).transpose(0, 2, 3, 1)) * scale
        v =  v.reshape(B, -1, nh, hd).transpose(0, 2, 1, 3)

        attn = mx.softmax(q @ k, axis=-1, precise=True)
        out  = (attn @ v).transpose(0, 2, 1, 3).reshape(B, T, C)
        return self.out(out)


class _ResidualBlock(nn.Module):
    def __init__(self, n_state: int, n_head: int):
        super().__init__()
        self.attn    = _MHA(n_state, n_head)
        self.attn_ln = nn.LayerNorm(n_state)
        n_mlp = n_state * 4
        self.mlp1    = nn.Linear(n_state, n_mlp)
        self.mlp2    = nn.Linear(n_mlp, n_state)
        self.mlp_ln  = nn.LayerNorm(n_state)

    def __call__(self, x, mask=None):
        x = x + self.attn(self.attn_ln(x), mask=mask)
        x = x + self.mlp2(nn.gelu(self.mlp1(self.mlp_ln(x))))
        return x


class AudioEncoderMLX(nn.Module):
    """Whisper tiny audio encoder."""

    def __init__(self, n_mels=N_MELS, n_ctx=N_CTX,
                 n_state=N_STATE, n_head=N_HEAD, n_layer=N_LAYER):
        super().__init__()
        self.conv1 = nn.Conv1d(n_mels, n_state, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(n_state, n_state, kernel_size=3, stride=2, padding=1)
        self._pos_emb = _sinusoids(n_ctx, n_state)
        self.blocks  = [_ResidualBlock(n_state, n_head) for _ in range(n_layer)]
        self.ln_post = nn.LayerNorm(n_state)

    def __call__(self, mel: mx.array) -> mx.array:
        """mel: (B, T_frames, N_MELS) → (B, T_ctx, N_STATE)"""
        x = nn.gelu(self.conv1(mel))
        x = nn.gelu(self.conv2(x))
        # Clip to N_CTX (padding can produce T_ctx = N_CTX+1); add batch dim to pos_emb
        x = x[:, :N_CTX]
        x = x + self._pos_emb[None, :x.shape[1]]
        for block in self.blocks:
            x = block(x)
        return self.ln_post(x)


# ── Mel spectrogram helper ────────────────────────────────────────────────────

def _log_mel_spectrogram(audio: np.ndarray, n_mels: int = 80) -> np.ndarray:
    """Compute log-mel spectrogram matching OpenAI Whisper's preprocessing."""
    try:
        import torch
        import torch.nn.functional as F
        waveform = torch.from_numpy(audio).float()
        # Whisper uses n_fft=400, hop=160, win=400 at 16kHz
        stft = torch.stft(
            waveform, n_fft=400, hop_length=HOP_LENGTH, win_length=400,
            window=torch.hann_window(400), return_complex=True,
        )
        magnitudes = stft.abs() ** 2
        mel_filters = _build_mel_filters(n_mels, 400 // 2 + 1, SAMPLE_RATE)
        mel = torch.from_numpy(mel_filters) @ magnitudes
        log_mel = torch.clamp(mel, min=1e-10).log10()
        log_mel = torch.maximum(log_mel, log_mel.max() - 8.0)
        log_mel = (log_mel + 4.0) / 4.0
        return log_mel.numpy()
    except Exception:
        # Fallback: use librosa
        import librosa
        mel = librosa.feature.melspectrogram(
            y=audio, sr=SAMPLE_RATE, n_mels=n_mels, n_fft=400,
            hop_length=HOP_LENGTH, win_length=400,
        )
        log_mel = librosa.power_to_db(mel, ref=np.max) / 40.0 + 1.0
        return log_mel.astype(np.float32)


def _build_mel_filters(n_mels: int, n_freqs: int, sample_rate: int) -> np.ndarray:
    """Build mel filterbank (matches librosa/whisper defaults)."""
    try:
        import librosa
        return librosa.filters.mel(sr=sample_rate, n_fft=(n_freqs - 1) * 2,
                                   n_mels=n_mels).astype(np.float32)
    except ImportError:
        # Simple triangular approximation
        return np.eye(n_mels, n_freqs, dtype=np.float32)


# ── High-level Audio2Feature interface ───────────────────────────────────────

class Audio2FeatureMLX:
    """
    Drop-in replacement for LatentSync's Audio2Feature using MLX.

    Usage:
        enc = Audio2FeatureMLX.from_checkpoint("checkpoints/whisper/tiny.pt")
        features = enc.audio2feat("audio.mp3")          # (T_ctx, 384)
        chunks   = enc.feature2chunks(features, fps=25) # list of (16, 384) per frame
    """

    def __init__(self, model: AudioEncoderMLX):
        self.model = model

    @classmethod
    def from_checkpoint(cls, ckpt_path: str | Path) -> "Audio2FeatureMLX":
        from .weights import load_whisper_weights
        model = AudioEncoderMLX()
        skipped = load_whisper_weights(model, ckpt_path)
        if skipped:
            print(f"[whisper] {len(skipped)} keys not loaded: {skipped[:3]}...")
        mx.eval(model.parameters())
        return cls(model)

    def audio2feat(self, audio_path: str) -> np.ndarray:
        """
        Load audio and return Whisper encoder features at 50 Hz.

        Mirrors MuseTalk/LatentSync's Audio2Feature._audio2feat():
        runs Whisper in overlapping 30-second chunks to cover the full audio,
        extracts intermediate encoder embeddings, and concatenates them.

        Returns: np.ndarray of shape (T_50hz, 5, N_STATE)
            T_50hz: number of 20ms frames at 50 Hz
            5:      mel time steps per 50-Hz frame
            N_STATE: 384 for Whisper tiny
        """
        audio = self._load_audio(audio_path)
        # Process in 30-second windows (Whisper context length)
        window_len  = SAMPLE_RATE * 30
        hop_len     = SAMPLE_RATE * 25  # 5-second overlap
        all_feats   = []

        pos = 0
        while pos < len(audio):
            chunk = audio[pos: pos + window_len]
            if len(chunk) < window_len:
                chunk = np.pad(chunk, (0, window_len - len(chunk)))

            log_mel = _log_mel_spectrogram(chunk, N_MELS)  # (N_MELS, T_mel)
            # MLX Conv1d expects (B, T, C) channel-last
            mel_mx = mx.array(log_mel.T[None])  # (1, T_mel, 80)
            feat = self.model(mel_mx)            # (1, T_ctx, 384)
            mx.eval(feat)
            feat_np = np.array(feat[0])          # (T_ctx, 384)

            # Reshape to (T_50hz, 5, 384): group every 5 mel-time-steps
            T_ctx_len = feat_np.shape[0]
            T_50hz    = T_ctx_len // 5
            feat_np   = feat_np[: T_50hz * 5].reshape(T_50hz, 5, N_STATE)

            # How much real audio this window covers (in 50Hz tokens)
            covered = int(min(hop_len, len(audio) - pos) * 50 / SAMPLE_RATE)
            all_feats.append(feat_np[:covered])
            pos += hop_len
            if pos >= len(audio):
                break

        return np.concatenate(all_feats, axis=0)  # (T_50hz_total, 5, 384)

    def feature2chunks(self, features: np.ndarray, fps: float = 25.0) -> List[np.ndarray]:
        """
        Build per-frame audio chunks using LatentSync's sliding window.

        Matches Audio2Feature.get_sliced_feature() with audio_feat_length=[2,2]:
          center = vid_idx * 50 / fps
          window = [center-4, center+6)  → 10 tokens
          each token is (5, 384) → flattened → (50, 384)

        Returns list of (50, 384) arrays — one per video frame.
        """
        T = len(features)            # number of 50-Hz tokens
        whisper_idx_multiplier = 50.0 / fps
        chunks = []
        i = 0
        while True:
            center = int(i * whisper_idx_multiplier)
            left   = center - AUDIO_FEAT_LENGTH[0] * TOKENS_PER_FEAT
            right  = center + (AUDIO_FEAT_LENGTH[1] + 1) * TOKENS_PER_FEAT
            window = []
            for idx in range(left, right):
                idx = max(0, min(T - 1, idx))
                window.append(features[idx])         # (5, 384)
            chunk = np.stack(window, axis=0)         # (10, 5, 384)
            chunk = chunk.reshape(-1, N_STATE)       # (50, 384)
            chunks.append(chunk)
            i += 1
            if center > T:
                break
        return chunks

    @staticmethod
    def _load_audio(path: str) -> np.ndarray:
        try:
            import librosa
            audio, _ = librosa.load(path, sr=SAMPLE_RATE, mono=True)
            return audio.astype(np.float32)
        except Exception:
            from decord import AudioReader
            ar = AudioReader(path, sample_rate=SAMPLE_RATE, mono=True)
            return ar[:].asnumpy().squeeze(0).astype(np.float32)
