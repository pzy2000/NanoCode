"""Tests for ContextPanel — token/cost/context display widget."""

from __future__ import annotations

import pytest


class TestContextStats:
    """Test the ContextStats dataclass that holds accumulated usage."""

    def test_initial_state(self):
        from nanocode.ui.context_panel import ContextStats

        s = ContextStats()
        assert s.total_input_tokens == 0
        assert s.total_output_tokens == 0
        assert s.total_cost == 0.0

    def test_add_usage_accumulates(self):
        from nanocode.ui.context_panel import ContextStats

        s = ContextStats()
        s.add(input_tokens=100, output_tokens=50, cost=0.10)
        s.add(input_tokens=200, output_tokens=80, cost=0.20)
        assert s.total_input_tokens == 300
        assert s.total_output_tokens == 130
        assert abs(s.total_cost - 0.30) < 1e-6

    def test_last_input_tokens_tracks_latest(self):
        from nanocode.ui.context_panel import ContextStats

        s = ContextStats()
        s.add(input_tokens=1000, output_tokens=50, cost=0.01)
        s.add(input_tokens=3313, output_tokens=100, cost=0.02)
        assert s.last_input_tokens == 3313

    def test_reset_clears_all(self):
        from nanocode.ui.context_panel import ContextStats

        s = ContextStats()
        s.add(input_tokens=500, output_tokens=100, cost=0.50)
        s.reset()
        assert s.total_input_tokens == 0
        assert s.total_output_tokens == 0
        assert s.total_cost == 0.0
        assert s.last_input_tokens == 0

    def test_to_dict(self):
        from nanocode.ui.context_panel import ContextStats

        s = ContextStats()
        s.add(input_tokens=100, output_tokens=50, cost=0.10)
        d = s.to_dict()
        assert d["total_input_tokens"] == 100
        assert d["total_output_tokens"] == 50
        assert abs(d["total_cost"] - 0.10) < 1e-6

    def test_from_dict(self):
        from nanocode.ui.context_panel import ContextStats

        d = {"total_input_tokens": 200, "total_output_tokens": 80, "total_cost": 0.25,
             "last_input_tokens": 200}
        s = ContextStats.from_dict(d)
        assert s.total_input_tokens == 200
        assert s.total_output_tokens == 80
        assert abs(s.total_cost - 0.25) < 1e-6

    def test_from_dict_missing_fields_defaults(self):
        from nanocode.ui.context_panel import ContextStats

        s = ContextStats.from_dict({})
        assert s.total_input_tokens == 0
        assert s.total_cost == 0.0


class TestContextPanelWidget:
    def test_import(self):
        from nanocode.ui.context_panel import ContextPanel
        assert ContextPanel is not None

    def test_initial_render_shows_context_header(self):
        from nanocode.ui.context_panel import ContextPanel

        panel = ContextPanel()
        text = panel.render_stats()
        assert "Context" in text

    def test_render_shows_zero_tokens_initially(self):
        from nanocode.ui.context_panel import ContextPanel

        panel = ContextPanel()
        text = panel.render_stats()
        assert "0" in text

    def test_update_usage_reflects_in_render(self):
        from nanocode.ui.context_panel import ContextPanel

        panel = ContextPanel()
        panel.update_usage(input_tokens=3313, output_tokens=100, model="gpt-4o")
        text = panel.render_stats()
        assert "3,313" in text or "3313" in text

    def test_render_shows_cost_when_model_known(self):
        from nanocode.ui.context_panel import ContextPanel

        panel = ContextPanel()
        panel.update_usage(input_tokens=1_000_000, output_tokens=0, model="gpt-4o")
        text = panel.render_stats()
        assert "$" in text
        assert "2.50" in text

    def test_render_shows_na_cost_for_unknown_model(self):
        from nanocode.ui.context_panel import ContextPanel

        panel = ContextPanel()
        panel.update_usage(input_tokens=1000, output_tokens=100, model="unknown-xyz")
        text = panel.render_stats()
        assert "N/A" in text or "n/a" in text.lower() or "$" not in text

    def test_render_shows_context_pct_for_known_model(self):
        from nanocode.ui.context_panel import ContextPanel
        from nanocode.pricing import PRICING

        panel = ContextPanel()
        window = PRICING["gpt-4o"][2]
        panel.update_usage(input_tokens=window // 2, output_tokens=0, model="gpt-4o")
        text = panel.render_stats()
        assert "50%" in text or "50.0%" in text

    def test_render_shows_na_pct_for_unknown_model(self):
        from nanocode.ui.context_panel import ContextPanel

        panel = ContextPanel()
        panel.update_usage(input_tokens=1000, output_tokens=0, model="unknown-xyz")
        text = panel.render_stats()
        assert "N/A" in text or "%" not in text

    def test_update_usage_accumulates_cost(self):
        from nanocode.ui.context_panel import ContextPanel

        panel = ContextPanel()
        panel.update_usage(input_tokens=1_000_000, output_tokens=0, model="gpt-4o")
        panel.update_usage(input_tokens=1_000_000, output_tokens=0, model="gpt-4o")
        text = panel.render_stats()
        # Total cost should be $5.00 (2 * $2.50)
        assert "5.00" in text

    def test_get_stats(self):
        from nanocode.ui.context_panel import ContextPanel

        panel = ContextPanel()
        panel.update_usage(input_tokens=500, output_tokens=100, model="gpt-4o")
        stats = panel.get_stats()
        assert stats.total_input_tokens == 500
        assert stats.total_output_tokens == 100

    def test_load_stats(self):
        from nanocode.ui.context_panel import ContextPanel, ContextStats

        panel = ContextPanel()
        s = ContextStats()
        s.add(input_tokens=9999, output_tokens=111, cost=1.23)
        panel.load_stats(s)
        stats = panel.get_stats()
        assert stats.total_input_tokens == 9999
        assert abs(stats.total_cost - 1.23) < 1e-6

    def test_context_pct_triggers_compact_warning(self):
        """render_stats should include a warning when context >= 80%."""
        from nanocode.ui.context_panel import ContextPanel
        from nanocode.pricing import PRICING

        panel = ContextPanel()
        window = PRICING["gpt-4o"][2]
        panel.update_usage(input_tokens=int(window * 0.85), output_tokens=0, model="gpt-4o")
        text = panel.render_stats()
        assert "!" in text or "warn" in text.lower() or "compact" in text.lower() or "85" in text
