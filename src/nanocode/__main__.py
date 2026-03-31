"""Entry point for nanocode."""

import sys

from nanocode.ui.app import NanoCodeApp


def main():
    provider = ""
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--provider" and i < len(sys.argv) - 1:
            provider = sys.argv[i + 1]
    app = NanoCodeApp(provider=provider)
    app.run()


if __name__ == "__main__":
    main()
