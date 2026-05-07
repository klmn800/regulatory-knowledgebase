"""
Cost tracking for Anthropic API calls.

Single source of truth for model pricing and cost arithmetic across apps.
Synthesis imports `MODEL_PRICING` and `calculate_cost`; QC and comparator
will migrate next, and use `Tracker` for stage-keyed accumulation.

Pricing is per-million tokens (USD). Update `MODEL_PRICING` when Anthropic
publishes new rates: https://www.anthropic.com/pricing
"""

import sys

MODEL_PRICING = {
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
    "claude-opus-4-20250805": {"input": 5.00, "output": 25.00},
}

# Fallback when a model isn't in MODEL_PRICING. Sonnet rates are the
# middle-of-the-road pick — better than silently zeroing the cost; per
# decision #3, don't halt work over a missing pricing entry.
_FALLBACK_RATES = {"input": 3.00, "output": 15.00}

_warned_models: set[str] = set()


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Compute cost in USD for an Anthropic API call.

    Returns 0.0 only if both token counts are zero. For unknown models, warns
    once per process to stderr and falls through to Sonnet rates.
    """
    rates = MODEL_PRICING.get(model)
    if rates is None:
        if model not in _warned_models:
            _warned_models.add(model)
            print(
                f"[cost_tracker] WARNING: model '{model}' not in MODEL_PRICING.\n"
                f"Using Sonnet rates as fallback. Cost reporting may be inaccurate.\n"
                f"Update tools/cost_tracker.py:MODEL_PRICING.\n"
                f"Reference: https://www.anthropic.com/pricing",
                file=sys.stderr,
                flush=True,
            )
        rates = _FALLBACK_RATES
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000


class Tracker:
    """Stage-keyed token + cost accumulator.

    Stages are declared up front so callers can roll up (`total()`) and
    attribute (`by_stage()`). Synthesis can pass stages=["synthesis"] or
    skip Tracker entirely and use `calculate_cost` directly. QC uses
    stages=["extractor", "judge", "cmr", "fns", "cfr"]; comparator uses
    stages=["session"].
    """

    def __init__(self, stages: list[str] | None = None):
        self.stages = list(stages) if stages else ["total"]
        self._data: dict[str, dict] = {
            stage: {"input_tokens": 0, "output_tokens": 0, "cost": 0.0}
            for stage in self.stages
        }

    def record(self, stage: str, model: str, usage) -> None:
        """Accumulate tokens and cost for a stage.

        `usage` is an Anthropic response.usage object with `.input_tokens`
        and `.output_tokens`. Raises ValueError on unknown stage so typos
        surface immediately rather than silently dropping cost.
        """
        if stage not in self._data:
            raise ValueError(
                f"Unknown stage {stage!r}; declared stages are {self.stages}"
            )
        in_tok = int(usage.input_tokens)
        out_tok = int(usage.output_tokens)
        bucket = self._data[stage]
        bucket["input_tokens"] += in_tok
        bucket["output_tokens"] += out_tok
        bucket["cost"] += calculate_cost(model, in_tok, out_tok)

    def total(self) -> dict:
        return {
            "input_tokens": sum(b["input_tokens"] for b in self._data.values()),
            "output_tokens": sum(b["output_tokens"] for b in self._data.values()),
            "cost": sum(b["cost"] for b in self._data.values()),
        }

    def by_stage(self) -> dict:
        return {stage: dict(bucket) for stage, bucket in self._data.items()}
