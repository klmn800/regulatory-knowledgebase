"""
Presentation Generator — converts reports to PowerPoint via Claude API.

Takes a report (text or file), calls Claude to generate a structured slide
outline, then calls pptx_writer to render the .pptx. Generic — works with
any report text, not tied to a specific program.

Usage:
    from tools.presentation import generate_presentation
    result = generate_presentation(report_text, "output.pptx")

CLI:
    python tools/presentation.py report.md -o slides.pptx
    python tools/presentation.py report.md --context "QC findings for Oct 2025"
    python tools/presentation.py report.md --max-slides 15
    python tools/presentation.py report.md --outline-only
"""

import argparse
import configparser
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import anthropic

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = PROJECT_ROOT / "prompts"
CONFIG_FILE = PROJECT_ROOT / "config.ini"

sys.path.insert(0, str(PROJECT_ROOT))
from tools.pptx_writer import generate_pptx, validate_outline


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PRICING = {
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
    "claude-opus-4-20250805": {"input": 5.00, "output": 25.00},
}


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")
    return config


def load_prompt(name: str) -> str:
    filepath = PROMPTS_DIR / f"{name}.md"
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = MODEL_PRICING.get(model, {"input": 3.00, "output": 15.00})
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000


# ============================================================
# RESULT TYPE
# ============================================================

@dataclass
class PresentationResult:
    """Result of a presentation generation run."""
    output_path: Path
    outline: dict
    slide_count: int
    input_tokens: int
    output_tokens: int
    cost: float
    duration_seconds: float
    model: str


# ============================================================
# JSON EXTRACTION
# ============================================================

def _extract_json(text: str) -> dict:
    """Extract JSON from Claude's response, handling code fences."""
    text = text.strip()
    # Try direct parse
    if text.startswith("{"):
        return json.loads(text)
    # Try extracting from code fence
    match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    # Try finding first { to last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start:end + 1])
    raise ValueError("Could not extract JSON from Claude's response")


# ============================================================
# OUTLINE GENERATION (Claude API)
# ============================================================

def report_to_outline(
    report: str,
    context: str | None = None,
    max_slides: int | None = None,
    config_overrides: dict | None = None,
) -> tuple[dict, int, int, float, str]:
    """Convert report text to a slide outline dict via Claude API.

    Args:
        report: The report text to convert.
        context: Optional framing/instructions for Claude.
        max_slides: Override max slide count.
        config_overrides: Override config values.

    Returns:
        Tuple of (outline_dict, input_tokens, output_tokens, cost, model).
    """
    config = load_config()

    model = config.get("presentation", "model", fallback="claude-haiku-4-5-20251001")
    max_tokens = config.getint("presentation", "max_tokens", fallback=4096)
    default_max_slides = config.getint("presentation", "max_slides", fallback=20)

    if config_overrides:
        model = config_overrides.get("model", model)
        max_tokens = int(config_overrides.get("max_tokens", max_tokens))
        default_max_slides = int(config_overrides.get("max_slides", default_max_slides))

    if max_slides is None:
        max_slides = default_max_slides

    api_key = config.get("api", "anthropic_api_key")
    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = load_prompt("presentation")

    # Build user message
    parts = []
    if context:
        parts.append(f"## Context\n{context}")
    parts.append(f"## Report\n{report}")
    parts.append(f"## Constraints\nMaximum {max_slides} slides.")
    user_message = "\n\n".join(parts)

    print(f"  Generating slide outline ({model})...", end="", flush=True)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    print(" done")

    raw_text = response.content[0].text.strip()
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    cost = calculate_cost(model, input_tokens, output_tokens)

    outline = _extract_json(raw_text)

    # Validate
    warnings = validate_outline(outline)
    if warnings:
        for w in warnings:
            print(f"  Warning: {w}", file=sys.stderr)

    return outline, input_tokens, output_tokens, cost, model


# ============================================================
# FULL PIPELINE
# ============================================================

def generate_presentation(
    report: str,
    output_path: Path | str,
    context: str | None = None,
    max_slides: int | None = None,
    template_path: Path | str | None = None,
    config_overrides: dict | None = None,
) -> PresentationResult:
    """Convert a report to a PowerPoint presentation.

    Args:
        report: The report text to convert into slides.
        output_path: Where to save the .pptx file.
        context: Optional context/instructions for Claude.
        max_slides: Override the maximum number of slides.
        template_path: Optional .pptx template for branding.
        config_overrides: Override config values.

    Returns:
        PresentationResult with output path, outline, and cost info.
    """
    start = time.time()
    output_path = Path(output_path)

    # Step 1: Generate outline via Claude
    outline, in_tok, out_tok, cost, model = report_to_outline(
        report, context, max_slides, config_overrides
    )

    # Step 2: Save outline JSON alongside the .pptx
    outline_path = output_path.with_suffix(".json")
    outline_path.parent.mkdir(parents=True, exist_ok=True)
    with open(outline_path, "w", encoding="utf-8") as f:
        json.dump(outline, f, indent=2, ensure_ascii=False)
    print(f"  Outline saved: {outline_path}")

    # Step 3: Render .pptx
    generate_pptx(outline, output_path, template_path=template_path)

    duration = time.time() - start
    slide_count = len(outline.get("slides", []))

    print(f"  Generated {slide_count}-slide presentation: {output_path}")
    print(f"  Cost: ${cost:.4f} | Tokens: {in_tok:,} in / {out_tok:,} out | {duration:.1f}s")

    return PresentationResult(
        output_path=output_path,
        outline=outline,
        slide_count=slide_count,
        input_tokens=in_tok,
        output_tokens=out_tok,
        cost=cost,
        duration_seconds=duration,
        model=model,
    )


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Convert a report to a PowerPoint presentation via Claude API."
    )
    parser.add_argument(
        "input",
        help="Path to report file (text, markdown, CSV, or JSON)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output .pptx path (default: same name as input with .pptx extension)"
    )
    parser.add_argument(
        "--context",
        help="Context or instructions for Claude (e.g., 'QC findings for Oct 2025')"
    )
    parser.add_argument(
        "--max-slides", type=int,
        help="Maximum number of slides (default: from config)"
    )
    parser.add_argument(
        "--template",
        help="Path to a .pptx template for branding"
    )
    parser.add_argument(
        "--outline-only", action="store_true",
        help="Generate the JSON outline only (no .pptx rendering)"
    )
    parser.add_argument(
        "--model",
        help="Override the Claude model to use"
    )

    args = parser.parse_args()

    # Read input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    report = input_path.read_text(encoding="utf-8")

    # Build config overrides
    overrides = {}
    if args.model:
        overrides["model"] = args.model

    if args.outline_only:
        outline, in_tok, out_tok, cost, model = report_to_outline(
            report,
            context=args.context,
            max_slides=args.max_slides,
            config_overrides=overrides or None,
        )
        # Save outline
        output_path = Path(args.output) if args.output else input_path.with_suffix(".json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(outline, f, indent=2, ensure_ascii=False)

        slide_count = len(outline.get("slides", []))
        print(f"  Outline saved: {output_path} ({slide_count} slides)")
        print(f"  Cost: ${cost:.4f} | Tokens: {in_tok:,} in / {out_tok:,} out")
    else:
        output_path = args.output
        if not output_path:
            output_path = input_path.with_suffix(".pptx")

        generate_presentation(
            report=report,
            output_path=output_path,
            context=args.context,
            max_slides=args.max_slides,
            template_path=args.template,
            config_overrides=overrides or None,
        )


if __name__ == "__main__":
    main()
