#!/usr/bin/env python3
"""
Animagine MCP REPL - Interactive CLI for testing MCP tools locally.

This is a convenience wrapper that can be run directly from the project root:
    python repl.py

For installed package usage:
    animagine-repl

Usage:
    python repl.py              # Start interactive REPL
    python repl.py --help       # Show help
    python repl.py --list       # List available tools

Examples in REPL:
    > validate_prompt("1girl, blue hair, masterpiece")
    > optimize_prompt(description="anime girl with silver hair")
    > explain_prompt("1girl, solo, masterpiece, best quality")
    > list_models()
    > generate_image("1girl, masterpiece", steps=20)
"""

import sys
from pathlib import Path

# Add src to path for local imports when running from project root
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

# Import and run the main REPL
from animagine_mcp.repl import main

if __name__ == "__main__":
    main()
