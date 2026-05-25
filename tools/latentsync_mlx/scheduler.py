"""
DDIM scheduler for LatentSync MLX.

Pure math — no learned weights. Ported from diffusers DDIMScheduler,
replacing torch.Tensor with mx.array throughout.
"""

import math
import numpy as np
import mlx.core as mx


class DDIMSchedulerMLX:
    """
    DDIM (Denoising Diffusion Implicit Models) scheduler.

    Matches the diffusers DDIMScheduler with beta_schedule="scaled_linear",
    clip_sample=False, set_alpha_to_one=False as used by LatentSync.
    """

    def __init__(
        self,
        num_train_timesteps: int = 1000,
        beta_start: float = 0.00085,
        beta_end: float = 0.012,
        beta_schedule: str = "scaled_linear",
        clip_sample: bool = False,
        set_alpha_to_one: bool = False,
    ):
        self.num_train_timesteps = num_train_timesteps
        self.clip_sample = clip_sample

        # Betas: scaled_linear = linear in sqrt space
        if beta_schedule == "scaled_linear":
            betas = np.linspace(beta_start**0.5, beta_end**0.5, num_train_timesteps, dtype=np.float32) ** 2
        elif beta_schedule == "linear":
            betas = np.linspace(beta_start, beta_end, num_train_timesteps, dtype=np.float32)
        else:
            raise ValueError(f"Unknown beta_schedule: {beta_schedule}")

        alphas = 1.0 - betas
        self.alphas_cumprod = np.cumprod(alphas)

        # final alpha_cumprod for t=-1 (initial noise)
        self.final_alpha_cumprod = 1.0 if set_alpha_to_one else float(self.alphas_cumprod[0])

        self.timesteps: np.ndarray | None = None
        self.num_inference_steps: int | None = None

    def set_timesteps(self, num_inference_steps: int):
        self.num_inference_steps = num_inference_steps
        step_ratio = self.num_train_timesteps // num_inference_steps
        # Timesteps from high → low (DDIM denoises in this order)
        timesteps = (np.arange(0, num_inference_steps) * step_ratio).round()[::-1].copy().astype(np.int64)
        self.timesteps = timesteps

    def _get_prev_timestep(self, t: int) -> int:
        prev_t = t - self.num_train_timesteps // self.num_inference_steps
        return prev_t

    def step(
        self,
        noise_pred: mx.array,
        t: int,
        latents: mx.array,
        eta: float = 0.0,
    ) -> mx.array:
        """
        One DDIM denoising step.

        Args:
            noise_pred: model output (predicted noise), shape (..., C, H, W)
            t: current timestep integer
            latents: current latents
            eta: stochasticity factor (0 = deterministic DDIM, 1 = DDPM)

        Returns:
            Denoised latents for the previous timestep.
        """
        prev_t = self._get_prev_timestep(t)

        alpha_prod_t = float(self.alphas_cumprod[t])
        alpha_prod_t_prev = float(self.alphas_cumprod[prev_t]) if prev_t >= 0 else self.final_alpha_cumprod

        beta_prod_t = 1 - alpha_prod_t

        # Predicted x0
        pred_original_sample = (latents - (beta_prod_t**0.5) * noise_pred) / (alpha_prod_t**0.5)

        if self.clip_sample:
            pred_original_sample = mx.clip(pred_original_sample, -1, 1)

        # DDIM direction
        pred_sample_direction = ((1 - alpha_prod_t_prev) ** 0.5) * noise_pred

        # Previous sample
        prev_sample = (alpha_prod_t_prev**0.5) * pred_original_sample + pred_sample_direction

        return prev_sample

    @property
    def init_noise_sigma(self) -> float:
        return float(max(self.alphas_cumprod))
