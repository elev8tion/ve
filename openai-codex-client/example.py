from openai_codex import OpenAICodexOAuthClient

client = OpenAICodexOAuthClient()

print("Status:", client.status())

# Uncomment after login:
# token = client.get_access_token()
# print("Got access token (first 20 chars):", token[:20] + "...")