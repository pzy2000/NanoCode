"""Model pricing table and cost/context utilities."""

from __future__ import annotations

# (input_$/1M_tokens, output_$/1M_tokens, context_window)
PRICING: dict[str, tuple[float, float, int]] = {
    "gpt-4o":               (2.50,  10.00, 128_000),
    "gpt-4o-mini":          (0.15,   0.60, 128_000),
    "gpt-4.5-preview":      (75.0, 150.0,  128_000),
    "MiniMax/MiniMax-M2.5": (0.30,   1.20, 204_800),
    "qwen3.5-plus":         (0.50,   2.00, 128_000),
    "claude-opus-4-5":      (15.0,  75.0,  200_000),
    "claude-sonnet-4-5":    (3.00,  15.0,  200_000),
    "claude-haiku-4-5":     (0.80,   4.0,  200_000),
}


def calc_cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """Return USD cost for the given token counts, or None for unknown models."""
    entry = PRICING.get(model)
    if entry is None:
        return None
    in_price, out_price, _ = entry
    return (input_tokens * in_price + output_tokens * out_price) / 1_000_000


def context_pct(model: str, input_tokens: int) -> float | None:
    """Return percentage of context window used, or None for unknown models."""
    entry = PRICING.get(model)
    if entry is None:
        return None
    _, _, window = entry
    if window == 0:
        return 0.0
    return input_tokens / window * 100.0


def context_window(model: str) -> int | None:
    """Return context window size in tokens, or None for unknown models."""
    entry = PRICING.get(model)
    if entry is None:
        return None
    return entry[2]
