"""Example: Generate images using Codex OAuth (no API key)."""

from openai_codex import OpenAICodexOAuthClient, OpenAICodexMediaClient
import base64
from pathlib import Path

def main():
    oauth = OpenAICodexOAuthClient()
    if not oauth.has_valid_tokens():
        print("Please run: openai-codex login")
        return

    media = OpenAICodexMediaClient(oauth)

    result = media.generate_image(
        prompt="A cyberpunk cat wearing sunglasses, neon lights, rainy night",
        aspect_ratio="landscape",   # landscape | square | portrait
        quality="medium",           # low | medium | high
    )

    if result["success"]:
        print(f"Success! Size: {result['size']}, Quality: {result['quality']}")
        # Save the image
        img_data = base64.b64decode(result["image_b64"])
        out_path = Path("generated_image.png")
        out_path.write_bytes(img_data)
        print(f"Saved to {out_path}")
    else:
        print("Error:", result["error"])


if __name__ == "__main__":
    main()