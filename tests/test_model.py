"""Tests for /model command — written BEFORE implementation (TDD)."""

import pytest


class TestPresetModels:
    def test_preset_models_exist(self):
        from nanocode.ui.app import PRESET_MODELS

        assert "openai" in PRESET_MODELS
        assert "anthropic" in PRESET_MODELS

    def test_openai_presets_include_required(self):
        from nanocode.ui.app import PRESET_MODELS

        models = PRESET_MODELS["openai"]
        assert any("gpt" in m.lower() for m in models)
        assert any("minimax" in m.lower() or "Minimax" in m for m in models)
        assert any("qwen" in m.lower() for m in models)

    def test_anthropic_presets_exist(self):
        from nanocode.ui.app import PRESET_MODELS

        assert len(PRESET_MODELS["anthropic"]) >= 2

    def test_all_presets_are_strings(self):
        from nanocode.ui.app import PRESET_MODELS

        for provider, models in PRESET_MODELS.items():
            for m in models:
                assert isinstance(m, str) and len(m) > 0


class TestEngineSetModel:
    def test_set_model_updates_backend(self):
        from unittest.mock import MagicMock
        from nanocode.engine import Engine

        backend = MagicMock()
        backend.model = "gpt-4o"
        engine = Engine(backend)
        engine.set_model("gpt-4o-mini")
        assert engine.backend.model == "gpt-4o-mini"

    def test_get_model_returns_current(self):
        from unittest.mock import MagicMock
        from nanocode.engine import Engine

        backend = MagicMock()
        backend.model = "gpt-4o"
        engine = Engine(backend)
        assert engine.get_model() == "gpt-4o"


class TestFormatModelList:
    def test_format_model_list_shows_current(self):
        from nanocode.ui.app import format_model_list

        result = format_model_list(["gpt-4o", "gpt-4o-mini"], current="gpt-4o")
        assert "gpt-4o" in result
        assert "1" in result  # index

    def test_format_model_list_marks_active(self):
        from nanocode.ui.app import format_model_list

        result = format_model_list(["gpt-4o", "gpt-4o-mini"], current="gpt-4o-mini")
        # current model should be marked somehow
        assert "gpt-4o-mini" in result

    def test_format_model_list_shows_all(self):
        from nanocode.ui.app import format_model_list

        models = ["gpt-4o", "gpt-4o-mini", "Minimax/MiniMax-M2.5", "qwen3.5-plus"]
        result = format_model_list(models, current="gpt-4o")
        for m in models:
            assert m in result

    def test_format_model_list_has_usage_hint(self):
        from nanocode.ui.app import format_model_list

        result = format_model_list(["gpt-4o"], current="gpt-4o")
        assert "/model" in result


class TestHandleModelCommand:
    def _make_app(self, model="gpt-4o", provider="openai"):
        """Create a minimal app-like object for testing."""
        from unittest.mock import MagicMock
        from nanocode.engine import Engine

        backend = MagicMock()
        backend.model = model
        engine = Engine(backend)

        app = MagicMock()
        app.engine = engine
        app._provider = provider
        return app

    def test_model_no_arg_returns_list(self):
        from nanocode.ui.app import handle_model_command, PRESET_MODELS
        from unittest.mock import MagicMock
        from nanocode.engine import Engine

        backend = MagicMock()
        backend.model = "gpt-4o"
        engine = Engine(backend)
        result = handle_model_command("/model", engine, "openai")
        assert result is not None
        assert "gpt-4o" in result

    def test_model_switch_by_name(self):
        from nanocode.ui.app import handle_model_command
        from unittest.mock import MagicMock
        from nanocode.engine import Engine

        backend = MagicMock()
        backend.model = "gpt-4o"
        engine = Engine(backend)
        result = handle_model_command("/model gpt-4o-mini", engine, "openai")
        assert engine.get_model() == "gpt-4o-mini"
        assert result is not None
        assert "gpt-4o-mini" in result

    def test_model_switch_by_index(self):
        from nanocode.ui.app import handle_model_command, PRESET_MODELS
        from unittest.mock import MagicMock
        from nanocode.engine import Engine

        backend = MagicMock()
        backend.model = "gpt-4o"
        engine = Engine(backend)
        # Switch to model #2 (index 1)
        result = handle_model_command("/model 2", engine, "openai")
        expected = PRESET_MODELS["openai"][1]
        assert engine.get_model() == expected
        assert expected in result

    def test_model_unknown_name_returns_error(self):
        from nanocode.ui.app import handle_model_command
        from unittest.mock import MagicMock
        from nanocode.engine import Engine

        backend = MagicMock()
        backend.model = "gpt-4o"
        engine = Engine(backend)
        result = handle_model_command("/model nonexistent-model-xyz", engine, "openai")
        # Should still switch (custom model) or show error
        assert result is not None

    def test_model_index_out_of_range(self):
        from nanocode.ui.app import handle_model_command
        from unittest.mock import MagicMock
        from nanocode.engine import Engine

        backend = MagicMock()
        backend.model = "gpt-4o"
        engine = Engine(backend)
        result = handle_model_command("/model 999", engine, "openai")
        assert result is not None
        assert (
            "invalid" in result.lower() or "range" in result.lower() or "999" in result
        )

    def test_model_not_command_returns_none(self):
        from nanocode.ui.app import handle_model_command
        from unittest.mock import MagicMock
        from nanocode.engine import Engine

        backend = MagicMock()
        backend.model = "gpt-4o"
        engine = Engine(backend)
        assert handle_model_command("/agent claude", engine, "openai") is None
        assert handle_model_command("hello", engine, "openai") is None
