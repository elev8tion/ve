# openai-codex-client

Standalone OpenAI Codex (ChatGPT) OAuth client with image generation.

This package replicates the `openai-codex` OAuth + image generation experience from Hermes Agent.

## Features

- Device code OAuth login (same flow as Hermes)
- Secure token storage + auto-refresh
- Image generation via Codex Responses API (`gpt-image-2`)
- Quality tiers: `low` / `medium` / `high`
- Aspect ratios: `landscape` / `square` / `portrait`

## Installation

```bash
cd openai-codex-client
pip install -e .
```

## CLI

```bash
openai-codex login
openai-codex status
openai-codex logout
```

## Programmatic Usage

```python
from openai_codex import OpenAICodexOAuthClient, OpenAICodexMediaClient

oauth = OpenAICodexOAuthClient()
media = OpenAICodexMediaClient(oauth)

# Generate image
result = media.generate_image(
    prompt="A cyberpunk samurai standing in the rain",
    aspect_ratio="landscape",   # landscape | square | portrait
    quality="high",             # low | medium | high
)

if result["success"]:
    print("Image generated successfully")
    # result["image_b64"] contains the base64 PNG
else:
    print("Error:", result["error"])
```

The OAuth client handles authentication. The media client uses the exact same parameters and streaming logic as Hermes' `openai-codex` image provider.