"""Tests for pricing module — cost calculation and context window tracking."""

from __future__ import annotations

import pytest

from nanocode.pricing import calc_cost, context_pct, context_window, PRICING


class TestPricingTable:
    def test_known_models_exist(self):
        for model in [
            "gpt-4o", "gpt-4o-mini", "gpt-4.5-preview",
            "claude-opus-4-5", "claude-sonnet-4-5", "claude-haiku-4-5",
            "MiniMax/MiniMax-M2.5",
        ]:
            assert model in PRICING, f"Missing pricing for {model}"

    def test_pricing_tuple_has_three_fields(self):
        for model, entry in PRICING.items():
            assert len(entry) == 3, f"{model} pricing should have (in, out, window)"

    def test_minimax_pricing(self):
        inp, out, window = PRICING["MiniMax/MiniMax-M2.5"]
        assert inp == 0.30
        assert out == 1.20
        assert window == 204_800

    def test_gpt4o_pricing(self):
        inp, out, window = PRICING["gpt-4o"]
        assert inp == 2.50
        assert out == 10.00
        assert window == 128_000

    def test_claude_sonnet_pricing(self):
        inp, out, window = PRICING["claude-sonnet-4-5"]
        assert inp == 3.00
        assert out == 15.0
        assert window == 200_000


class TestCalcCost:
    def test_zero_tokens_zero_cost(self):
        assert calc_cost("gpt-4o", 0, 0) == 0.0

    def test_known_model_returns_float(self):
        cost = calc_cost("gpt-4o", 1_000_000, 0)
        assert isinstance(cost, float)
        assert abs(cost - 2.50) < 0.001

    def test_output_tokens_cost(self):
        cost = calc_cost("gpt-4o", 0, 1_000_000)
        assert abs(cost - 10.00) < 0.001

    def test_combined_cost(self):
        # 500k input + 500k output for gpt-4o-mini
        # = 500k * 0.15/1M + 500k * 0.60/1M = 0.075 + 0.30 = 0.375
        cost = calc_cost("gpt-4o-mini", 500_000, 500_000)
        assert abs(cost - 0.375) < 0.001

    def test_unknown_model_returns_none(self):
        assert calc_cost("unknown-model-xyz", 1000, 1000) is None

    def test_minimax_cost(self):
        # 1M input tokens = $0.30
        cost = calc_cost("MiniMax/MiniMax-M2.5", 1_000_000, 0)
        assert abs(cost - 0.30) < 0.001

    def test_small_token_count(self):
        # 3313 input tokens for gpt-4o = 3313 * 2.50 / 1_000_000
        cost = calc_cost("gpt-4o", 3313, 0)
        expected = 3313 * 2.50 / 1_000_000
        assert abs(cost - expected) < 1e-6


class TestContextPct:
    def test_zero_tokens_zero_pct(self):
        assert context_pct("gpt-4o", 0) == 0.0

    def test_full_context_100_pct(self):
        window = PRICING["gpt-4o"][2]
        assert context_pct("gpt-4o", window) == 100.0

    def test_half_context(self):
        window = PRICING["gpt-4o"][2]
        pct = context_pct("gpt-4o", window // 2)
        assert abs(pct - 50.0) < 0.01

    def test_unknown_model_returns_none(self):
        assert context_pct("unknown-model-xyz", 1000) is None

    def test_minimax_context_window(self):
        pct = context_pct("MiniMax/MiniMax-M2.5", 204_800)
        assert abs(pct - 100.0) < 0.01

    def test_returns_float(self):
        result = context_pct("gpt-4o", 1000)
        assert isinstance(result, float)


class TestContextWindow:
    def test_known_model_returns_int(self):
        w = context_window("gpt-4o")
        assert w == 128_000

    def test_unknown_model_returns_none(self):
        assert context_window("unknown-xyz") is None

    def test_claude_window(self):
        assert context_window("claude-sonnet-4-5") == 200_000
