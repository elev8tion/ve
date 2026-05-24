from __future__ import annotations

import argparse
import sys

from .client import OpenAICodexOAuthClient


def main():
    parser = argparse.ArgumentParser(
        prog="openai-codex",
        description="OpenAI Codex (ChatGPT) OAuth client"
    )
    subparsers = parser.add_subparsers(dest="command")

    # login
    subparsers.add_parser("login", help="Login with ChatGPT account")

    # logout
    subparsers.add_parser("logout", help="Logout and remove tokens")

    # status
    subparsers.add_parser("status", help="Show authentication status")

    args = parser.parse_args()

    client = OpenAICodexOAuthClient()

    if args.command == "login":
        client.login()
    elif args.command == "logout":
        client.logout()
    elif args.command == "status":
        status = client.status()
        if status.get("authenticated"):
            print("✅ Authenticated with OpenAI Codex (ChatGPT OAuth)")
        else:
            print("❌ Not authenticated. Run `openai-codex login`")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()