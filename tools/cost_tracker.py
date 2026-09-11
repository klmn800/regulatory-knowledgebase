"""
Cost tracking for Anthropic API calls.

Single source of truth for model pricing and cost arithmetic across apps.
Synthesis imports `MODEL_PRICING` and `calculate_cost`; QC and comparator
will migrate next, and use `Tracker` for stage-keyed accumulation.

Pricing is per-million tokens (USD). Update `MODEL_PRICING` when Anthropic
publishes new rates: https://www.anthropic.com/pricing
"""

import sys

# Rates from Anthropic's published model table as of 2026-06-24. Both the
# alias and the dated ID are listed where config.ini uses dated IDs.
MODEL_PRICING = {
    "claude-fable-5-1": {"input": 10.00, "output": 50.00},
    "claude-fable-5": {"input": 10.00, "output": 50.00},
    "claude-opus-5": {"input": 5.00, "output": 25.00},
    "claude-opus-4-8": {"input": 5.00, "output": 25.00},
    "claude-opus-4-7": {"input": 5.00, "output": 25.00},
    "claude-opus-4-6": {"input": 5.00, "output": 25.00},
    "claude-sonnet-5": {"input": 2.00, "output": 10.00},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4-5-20250929": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
}

# Unknown model in a known family (e.g. a new Opus release not yet in the
# table) is priced at that family's newest listed rates — a far closer
# estimate than one flat rate for every family.
_FAMILY_STAND_IN = {
    "fable": "claude-fable-5-1",
    "opus": "claude-opus-5",
    "sonnet": "claude-sonnet-5",
    "haiku": "claude-haiku-4-5",
}

# Last resort when no family can be read from the model ID. Per decision #3,
# don't halt work over a missing pricing entry — estimate and flag it.
_GENERIC_RATES = {"input": 3.00, "output": 15.00}

_warned_models: set[str] = set()


def resolve_rates(model: str) -> tuple[dict, str | None]:
    """Return (rates, stand_in) for a model.

    stand_in is None when the model has its own MODEL_PRICING entry (exact
    cost). Otherwise it names what the rates were borrowed from — a family
    stand-in model ID, or "generic" — and any cost computed from them is an
    estimate.
    """
    rates = MODEL_PRICING.get(model)
    if rates is not None:
        return rates, None
    tokens = (model or "").lower().replace(".", "-").split("-")
    for family, stand_in in _FAMILY_STAND_IN.items():
        if family in tokens:
            return MODEL_PRICING[stand_in], stand_in
    return _GENERIC_RATES, "generic"


def estimate_note(model: str) -> str:
    """Human-readable explanation when `model`'s cost is an estimate, else ""."""
    _, stand_in = resolve_rates(model)
    if stand_in is None:
        return ""
    basis = ("generic $3/$15 rates" if stand_in == "generic"
             else f"{stand_in} rates")
    return (f"Estimated: {model} is not in the pricing table "
            f"(tools/cost_tracker.py), so it is priced at {basis}.")


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Compute cost in USD for an Anthropic API call.

    Returns 0.0 only if both token counts are zero. For models without a
    MODEL_PRICING entry, uses resolve_rates() stand-in rates and warns once
    per process to stderr; UIs surface the same fact via estimate_note().
    """
    rates, stand_in = resolve_rates(model)
    if stand_in is not None and model not in _warned_models:
        _warned_models.add(model)
        print(
            f"[cost_tracker] WARNING: {estimate_note(model)}\n"
            f"Add it to tools/cost_tracker.py:MODEL_PRICING.\n"
            f"Reference: https://www.anthropic.com/pricing",
            file=sys.stderr,
            flush=True,
        )
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
