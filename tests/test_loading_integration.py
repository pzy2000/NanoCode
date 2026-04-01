"""Integration test for LoadingIndicator visibility in ChatView."""

import pytest
from textual.pilot import Pilot


@pytest.mark.asyncio
async def test_loading_indicator_on_mount_initializes_display():
    """Test that LoadingIndicator.on_mount() sets display=False."""
    from nanocode.ui.loading import LoadingIndicator
    from textual.app import App, ComposeResult

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield LoadingIndicator(id="loading")

    app = TestApp()
    async with app.run_test() as pilot:
        indicator = app.query_one("#loading", LoadingIndicator)

        # After mount, display should be False
        assert indicator.display is False
        assert indicator.is_active is False


@pytest.mark.asyncio
async def test_loading_indicator_visible_in_chat_view():
    """Test that LoadingIndicator is visible when active in ChatView."""
    from nanocode.ui.chat_view import ChatView
    from nanocode.ui.loading import LoadingIndicator
    from textual.app import App, ComposeResult

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield ChatView(id="chat-view")

    app = TestApp()
    async with app.run_test() as pilot:
        chat = app.query_one("#chat-view", ChatView)
        indicator = chat.query_one("#loading", LoadingIndicator)

        # Initially hidden
        assert indicator.display is False
        assert indicator.is_active is False

        # Start loading
        chat.start_loading("thinking")
        await pilot.pause()

        # Should be visible
        assert indicator.display is True
        assert indicator.is_active is True
        assert indicator.phrase != ""

        # Stop loading
        chat.stop_loading()
        await pilot.pause()

        # Should be hidden
        assert indicator.display is False
        assert indicator.is_active is False


@pytest.mark.asyncio
async def test_loading_indicator_renders_content_when_active():
    """Test that LoadingIndicator renders visible content when active."""
    from nanocode.ui.chat_view import ChatView
    from nanocode.ui.loading import LoadingIndicator
    from textual.app import App, ComposeResult

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield ChatView(id="chat-view")

    app = TestApp()
    async with app.run_test() as pilot:
        chat = app.query_one("#chat-view", ChatView)
        indicator = chat.query_one("#loading", LoadingIndicator)

        # Start loading
        chat.start_loading("tool")
        await pilot.pause()

        # Render should produce non-empty content
        rendered = indicator.render()
        assert rendered.plain != ""
        from nanocode.ui.loading import SPINNER_FRAMES
        assert any(f in rendered.plain for f in SPINNER_FRAMES)  # spinner char
        assert indicator.phrase in rendered.plain
