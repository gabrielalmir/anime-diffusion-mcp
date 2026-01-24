#!/usr/bin/env python3
"""
Animagine MCP REPL - Interactive CLI for testing MCP tools locally.

Usage:
    animagine-repl              # Start interactive REPL (if installed)
    python -m animagine_mcp.repl # Alternative
    python repl.py              # From project root

Examples in REPL:
    > validate_prompt("1girl, blue hair, masterpiece")
    > optimize_prompt(description="anime girl with silver hair")
    > explain_prompt("1girl, solo, masterpiece, best quality")
    > list_models()
    > generate_image("1girl, masterpiece", steps=20)
"""

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any

# Try to enable readline for better input handling
try:
    import readline  # noqa: F401
except ImportError:
    pass  # readline not available on Windows by default


# =============================================================================
# Tool Wrappers
# =============================================================================

def validate_prompt(
    prompt: str,
    width: int = 832,
    height: int = 1216,
    negative_prompt: str | None = None,
) -> dict:
    """Validate a prompt against Animagine XL rules."""
    from .prompt import validate_prompt as _validate
    result = _validate(prompt=prompt, width=width, height=height, negative_prompt=negative_prompt)
    return result.model_dump()


def optimize_prompt(
    description: str | None = None,
    prompt: str | None = None,
) -> dict:
    """Optimize a prompt for Animagine XL."""
    from .prompt import optimize_prompt as _optimize
    result = _optimize(description=description, prompt=prompt)
    return result.model_dump()


def explain_prompt(prompt: str) -> dict:
    """Explain what each tag in a prompt does."""
    from .prompt import explain_prompt as _explain
    result = _explain(prompt)
    return result.model_dump()


def list_models() -> dict:
    """List available checkpoints and LoRAs."""
    from .diffusion.pipeline import get_pipeline
    pipeline = get_pipeline()
    return pipeline.list_available_models()


def load_checkpoint(checkpoint: str | None = None) -> dict:
    """Pre-load a checkpoint into GPU memory."""
    from .diffusion.pipeline import get_pipeline
    pipeline = get_pipeline()
    return pipeline.load_checkpoint(checkpoint)


def unload_loras() -> dict:
    """Unload all LoRA weights from the current pipeline."""
    from .diffusion.pipeline import get_pipeline
    pipeline = get_pipeline()
    return pipeline.unload_loras()


def generate_image(
    prompt: str,
    negative_prompt: str | None = None,
    checkpoint: str | None = None,
    loras: list[str] | None = None,
    lora_scales: list[float] | None = None,
    width: int = 832,
    height: int = 1216,
    steps: int = 28,
    guidance_scale: float = 5.0,
    seed: int | None = None,
) -> dict:
    """Generate an image with Animagine XL 4.0."""
    from .diffusion.pipeline import get_pipeline
    pipeline = get_pipeline()

    lora_configs = None
    if loras:
        scales = lora_scales or [1.0] * len(loras)
        lora_configs = [
            {"filename": lora, "scale": scale}
            for lora, scale in zip(loras, scales)
        ]

    result = pipeline.generate(
        prompt=prompt,
        negative_prompt=negative_prompt,
        checkpoint=checkpoint,
        loras=lora_configs,
        width=width,
        height=height,
        steps=steps,
        guidance_scale=guidance_scale,
        seed=seed,
    )
    return result.model_dump()


def generate_image_from_image(
    image_path: str,
    prompt: str,
    negative_prompt: str | None = None,
    strength: float = 0.75,
    checkpoint: str | None = None,
    loras: list[str] | None = None,
    lora_scales: list[float] | None = None,
    steps: int = 28,
    guidance_scale: float = 5.0,
    seed: int | None = None,
) -> dict:
    """Generate an image using img2img transformation."""
    from .diffusion.pipeline import get_pipeline
    pipeline = get_pipeline()

    lora_configs = None
    if loras:
        scales = lora_scales or [1.0] * len(loras)
        lora_configs = [
            {"filename": lora, "scale": scale}
            for lora, scale in zip(loras, scales)
        ]

    result = pipeline.generate_img2img(
        image_path=image_path,
        prompt=prompt,
        negative_prompt=negative_prompt,
        strength=strength,
        checkpoint=checkpoint,
        loras=lora_configs,
        steps=steps,
        guidance_scale=guidance_scale,
        seed=seed,
    )
    return result.model_dump()


# =============================================================================
# Available Tools Registry
# =============================================================================

TOOLS = {
    "validate_prompt": validate_prompt,
    "optimize_prompt": optimize_prompt,
    "explain_prompt": explain_prompt,
    "list_models": list_models,
    "load_checkpoint": load_checkpoint,
    "unload_loras": unload_loras,
    "generate_image": generate_image,
    "generate_image_from_image": generate_image_from_image,
}

TOOL_DESCRIPTIONS = {
    "validate_prompt": "Validate a prompt against Animagine XL rules",
    "optimize_prompt": "Optimize/convert a prompt for Animagine XL",
    "explain_prompt": "Explain what each tag in a prompt does",
    "list_models": "List available checkpoints and LoRAs",
    "load_checkpoint": "Pre-load a checkpoint into GPU memory",
    "unload_loras": "Unload all LoRA weights from pipeline",
    "generate_image": "Generate an image from a prompt",
    "generate_image_from_image": "Transform an existing image (img2img)",
}


# =============================================================================
# REPL Implementation
# =============================================================================

class AnimagineREPL:
    """Interactive REPL for Animagine MCP tools."""

    def __init__(self, debug: bool = False):
        self.history: list[str] = []
        self.running = True
        self.debug = debug

    def print_banner(self):
        """Print welcome banner."""
        print("""
╔═══════════════════════════════════════════════════════════════════╗
║                    Animagine MCP REPL                             ║
║                  Interactive Tool Testing                         ║
╠═══════════════════════════════════════════════════════════════════╣
║  Commands:                                                        ║
║    help              - Show this help message                     ║
║    tools             - List available tools                       ║
║    tool <name>       - Show tool details and usage                ║
║    exit / quit / q   - Exit the REPL                              ║
║    clear             - Clear the screen                           ║
║    history           - Show command history                       ║
║                                                                   ║
║  Usage:                                                           ║
║    Call tools directly like Python functions:                     ║
║    > validate_prompt("1girl, blue hair, masterpiece")             ║
║    > optimize_prompt(description="anime girl")                    ║
║    > generate_image("1girl, masterpiece", steps=20)               ║
╚═══════════════════════════════════════════════════════════════════╝
""")

    def print_tools(self):
        """Print available tools."""
        print("\n Available Tools:")
        print("─" * 60)
        for name, desc in TOOL_DESCRIPTIONS.items():
            print(f"  {name:30} - {desc}")
        print("─" * 60)
        print("  Use 'tool <name>' for detailed usage\n")

    def print_tool_detail(self, name: str):
        """Print detailed info about a tool."""
        if name not in TOOLS:
            print(f"  Unknown tool: {name}")
            print(f"  Available: {', '.join(TOOLS.keys())}")
            return

        func = TOOLS[name]
        print(f"\n  {name}")
        print("─" * 60)
        print(f"  {TOOL_DESCRIPTIONS[name]}")
        print()

        # Print docstring
        if func.__doc__:
            print(f"  {func.__doc__}")
        print()

        # Print signature
        import inspect
        sig = inspect.signature(func)
        print(f"  Signature:")
        print(f"    {name}{sig}")
        print()

        # Print parameters
        print(f"  Parameters:")
        for param_name, param in sig.parameters.items():
            default = param.default
            if default is inspect.Parameter.empty:
                default_str = "(required)"
            else:
                default_str = f"= {repr(default)}"
            annotation = param.annotation
            if annotation is inspect.Parameter.empty:
                type_str = ""
            else:
                type_str = f": {annotation}"
            print(f"    {param_name}{type_str} {default_str}")
        print()

    def format_result(self, result: Any) -> str:
        """Format result for display."""
        if isinstance(result, dict):
            return json.dumps(result, indent=2, ensure_ascii=False, default=str)
        return str(result)

    def execute(self, line: str) -> Any:
        """Execute a command or tool call."""
        line = line.strip()

        if not line:
            return None

        # Handle special commands
        if line.lower() in ("exit", "quit", "q"):
            self.running = False
            print("  Goodbye!")
            return None

        if line.lower() == "help":
            self.print_banner()
            return None

        if line.lower() == "tools":
            self.print_tools()
            return None

        if line.lower().startswith("tool "):
            tool_name = line[5:].strip()
            self.print_tool_detail(tool_name)
            return None

        if line.lower() == "clear":
            print("\033[2J\033[H", end="")  # ANSI clear screen
            return None

        if line.lower() == "history":
            print("\n  Command History:")
            for i, cmd in enumerate(self.history[-20:], 1):
                print(f"  {i:3}. {cmd}")
            print()
            return None

        # Try to execute as Python expression
        try:
            # Create execution context with tools
            context = {
                **TOOLS,
                "print": print,
                "json": json,
                "Path": Path,
            }

            # Try eval first (for expressions)
            try:
                result = eval(line, context)
                return result
            except SyntaxError:
                # Try exec for statements
                exec(line, context)
                return None

        except Exception as e:
            print(f"\n  Error: {type(e).__name__}: {e}")
            if self.debug:
                traceback.print_exc()
            return None

    def run(self):
        """Run the REPL loop."""
        self.print_banner()

        # Check GPU status
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                print(f"  GPU: {gpu_name}")
            else:
                print("  GPU: Not available (CPU mode)")
        except ImportError:
            print("  GPU: PyTorch not installed")
        print()

        while self.running:
            try:
                # Read input
                line = input("\033[1;32manimagine>\033[0m ")

                if line.strip():
                    self.history.append(line)

                # Execute
                result = self.execute(line)

                # Print result
                if result is not None:
                    formatted = self.format_result(result)
                    print(f"\n{formatted}\n")

            except KeyboardInterrupt:
                print("\n  (Use 'exit' to quit)")
                continue

            except EOFError:
                print()
                self.running = False
                break


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Main entry point for the REPL CLI."""
    parser = argparse.ArgumentParser(
        description="Animagine MCP REPL - Interactive CLI for testing MCP tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  animagine-repl                     Start interactive REPL
  animagine-repl --list              List available tools
  animagine-repl --tool validate     Show validate_prompt usage
  animagine-repl -e "list_models()"  Execute single command

In REPL:
  > validate_prompt("1girl, blue hair, masterpiece")
  > optimize_prompt(description="anime girl with silver hair")
  > generate_image("1girl, masterpiece", steps=20)
        """
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available tools"
    )

    parser.add_argument(
        "--tool", "-t",
        metavar="NAME",
        help="Show detailed info about a specific tool"
    )

    parser.add_argument(
        "--execute", "-e",
        metavar="COMMAND",
        help="Execute a single command and exit"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show full stack traces on errors"
    )

    parser.add_argument(
        "--no-gpu-check",
        action="store_true",
        help="Skip GPU availability check on startup"
    )

    args = parser.parse_args()

    # Handle --list
    if args.list:
        print("\nAvailable Tools:")
        print("─" * 60)
        for name, desc in TOOL_DESCRIPTIONS.items():
            print(f"  {name:30} - {desc}")
        print("─" * 60)
        return

    # Handle --tool
    if args.tool:
        repl = AnimagineREPL(debug=args.debug)
        repl.print_tool_detail(args.tool)
        return

    # Handle --execute
    if args.execute:
        repl = AnimagineREPL(debug=args.debug)
        result = repl.execute(args.execute)
        if result is not None:
            print(repl.format_result(result))
        return

    # Start interactive REPL
    repl = AnimagineREPL(debug=args.debug)
    repl.run()


if __name__ == "__main__":
    main()
