"""
Tests for the UI components.

This module contains tests for the UI components functionality.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

from src.ui.components import (
    Button,
    TextField,
    Card,
    Dialog,
    Avatar,
    ThemeProvider,
    get_theme
)


class TestUIComponents:
    """Test suite for the UI components."""

    def test_button_render(self):
        """Test button rendering."""
        # Arrange
        on_click = MagicMock()
        button = Button(
            text="Click Me",
            on_click=on_click,
            variant="primary"
        )
        
        # Act
        rendered = button.render()
        
        # Assert
        assert "Click Me" in rendered
        assert "primary" in rendered
        assert "button" in rendered.lower()

    def test_button_click(self):
        """Test button click event."""
        # Arrange
        on_click = MagicMock()
        button = Button(
            text="Click Me",
            on_click=on_click,
            variant="primary"
        )
        
        # Act
        button.handle_click()
        
        # Assert
        on_click.assert_called_once()

    def test_button_disabled(self):
        """Test disabled button."""
        # Arrange
        on_click = MagicMock()
        button = Button(
            text="Click Me",
            on_click=on_click,
            variant="primary",
            disabled=True
        )
        
        # Act
        rendered = button.render()
        button.handle_click()
        
        # Assert
        assert "disabled" in rendered
        on_click.assert_not_called()

    def test_text_field_render(self):
        """Test text field rendering."""
        # Arrange
        on_change = MagicMock()
        text_field = TextField(
            label="Username",
            placeholder="Enter username",
            value="",
            on_change=on_change
        )
        
        # Act
        rendered = text_field.render()
        
        # Assert
        assert "Username" in rendered
        assert "Enter username" in rendered
        assert "input" in rendered.lower()

    def test_text_field_change(self):
        """Test text field change event."""
        # Arrange
        on_change = MagicMock()
        text_field = TextField(
            label="Username",
            placeholder="Enter username",
            value="",
            on_change=on_change
        )
        
        # Act
        text_field.handle_change("new_value")
        
        # Assert
        on_change.assert_called_once_with("new_value")
        assert text_field.value == "new_value"

    def test_card_render(self):
        """Test card rendering."""
        # Arrange
        card = Card(
            title="Card Title",
            content="Card content goes here",
            footer="Card Footer"
        )
        
        # Act
        rendered = card.render()
        
        # Assert
        assert "Card Title" in rendered
        assert "Card content goes here" in rendered
        assert "Card Footer" in rendered
        assert "card" in rendered.lower()

    def test_dialog_render(self):
        """Test dialog rendering."""
        # Arrange
        on_close = MagicMock()
        dialog = Dialog(
            title="Dialog Title",
            content="Dialog content goes here",
            is_open=True,
            on_close=on_close
        )
        
        # Act
        rendered = dialog.render()
        
        # Assert
        assert "Dialog Title" in rendered
        assert "Dialog content goes here" in rendered
        assert "dialog" in rendered.lower()
        assert "open" in rendered.lower()

    def test_dialog_close(self):
        """Test dialog close event."""
        # Arrange
        on_close = MagicMock()
        dialog = Dialog(
            title="Dialog Title",
            content="Dialog content goes here",
            is_open=True,
            on_close=on_close
        )
        
        # Act
        dialog.handle_close()
        
        # Assert
        on_close.assert_called_once()
        assert dialog.is_open is False

    def test_avatar_render(self):
        """Test avatar rendering."""
        # Arrange
        avatar = Avatar(
            name="John Doe",
            image_url="https://example.com/avatar.jpg",
            size="medium"
        )
        
        # Act
        rendered = avatar.render()
        
        # Assert
        assert "John Doe" in rendered
        assert "https://example.com/avatar.jpg" in rendered
        assert "medium" in rendered
        assert "avatar" in rendered.lower()

    def test_avatar_fallback(self):
        """Test avatar fallback when no image URL is provided."""
        # Arrange
        avatar = Avatar(
            name="John Doe",
            image_url=None,
            size="medium"
        )
        
        # Act
        rendered = avatar.render()
        
        # Assert
        assert "John Doe" in rendered
        assert "JD" in rendered  # Initials
        assert "avatar" in rendered.lower()

    def test_theme_provider(self):
        """Test theme provider."""
        # Arrange
        theme_provider = ThemeProvider(theme="dark")
        
        # Act
        rendered = theme_provider.render()
        
        # Assert
        assert "theme-provider" in rendered.lower()
        assert "dark" in rendered

    def test_get_theme(self):
        """Test getting theme values."""
        # Act
        light_theme = get_theme("light")
        dark_theme = get_theme("dark")
        
        # Assert
        assert light_theme is not None
        assert dark_theme is not None
        assert light_theme["colors"] is not None
        assert dark_theme["colors"] is not None
        assert light_theme["colors"]["background"] != dark_theme["colors"]["background"]


class TestVoiceComponents:
    """Test suite for the voice-specific UI components."""

    @pytest.fixture
    def mock_voice_service(self):
        """Create a mock voice service for testing."""
        mock_service = MagicMock()
        mock_service.state = "IDLE"
        mock_service.is_muted = False
        mock_service.connect = AsyncMock(return_value=True)
        mock_service.disconnect = AsyncMock(return_value=True)
        mock_service.start_listening = AsyncMock(return_value=True)
        mock_service.stop_listening = AsyncMock(return_value=True)
        mock_service.toggle_mute = AsyncMock(return_value=False)
        return mock_service

    def test_microphone_button_render(self, mock_voice_service):
        """Test microphone button rendering."""
        # Arrange
        from src.ui.voice_components import MicrophoneButton
        
        on_click = MagicMock()
        mic_button = MicrophoneButton(
            voice_service=mock_voice_service,
            on_click=on_click
        )
        
        # Act
        rendered = mic_button.render()
        
        # Assert
        assert "microphone" in rendered.lower()
        assert "button" in rendered.lower()

    @pytest.mark.asyncio
    async def test_microphone_button_click_idle(self, mock_voice_service):
        """Test microphone button click when voice service is idle."""
        # Arrange
        from src.ui.voice_components import MicrophoneButton
        
        mock_voice_service.state = "IDLE"
        on_click = MagicMock()
        mic_button = MicrophoneButton(
            voice_service=mock_voice_service,
            on_click=on_click
        )
        
        # Act
        await mic_button.handle_click()
        
        # Assert
        mock_voice_service.connect.assert_called_once()
        on_click.assert_called_once()

    @pytest.mark.asyncio
    async def test_microphone_button_click_connected(self, mock_voice_service):
        """Test microphone button click when voice service is connected."""
        # Arrange
        from src.ui.voice_components import MicrophoneButton
        
        mock_voice_service.state = "CONNECTED"
        on_click = MagicMock()
        mic_button = MicrophoneButton(
            voice_service=mock_voice_service,
            on_click=on_click
        )
        
        # Act
        await mic_button.handle_click()
        
        # Assert
        mock_voice_service.start_listening.assert_called_once()
        on_click.assert_called_once()

    @pytest.mark.asyncio
    async def test_microphone_button_click_listening(self, mock_voice_service):
        """Test microphone button click when voice service is listening."""
        # Arrange
        from src.ui.voice_components import MicrophoneButton
        
        mock_voice_service.state = "LISTENING"
        on_click = MagicMock()
        mic_button = MicrophoneButton(
            voice_service=mock_voice_service,
            on_click=on_click
        )
        
        # Act
        await mic_button.handle_click()
        
        # Assert
        mock_voice_service.stop_listening.assert_called_once()
        on_click.assert_called_once()

    def test_mute_button_render(self, mock_voice_service):
        """Test mute button rendering."""
        # Arrange
        from src.ui.voice_components import MuteButton
        
        on_click = MagicMock()
        mute_button = MuteButton(
            voice_service=mock_voice_service,
            on_click=on_click
        )
        
        # Act
        rendered = mute_button.render()
        
        # Assert
        assert "mute" in rendered.lower()
        assert "button" in rendered.lower()
        assert "unmuted" in rendered.lower()  # Default state

    @pytest.mark.asyncio
    async def test_mute_button_click(self, mock_voice_service):
        """Test mute button click."""
        # Arrange
        from src.ui.voice_components import MuteButton
        
        on_click = MagicMock()
        mute_button = MuteButton(
            voice_service=mock_voice_service,
            on_click=on_click
        )
        
        # Act
        await mute_button.handle_click()
        
        # Assert
        mock_voice_service.toggle_mute.assert_called_once()
        on_click.assert_called_once()

    def test_voice_status_indicator_render(self, mock_voice_service):
        """Test voice status indicator rendering."""
        # Arrange
        from src.ui.voice_components import VoiceStatusIndicator
        
        indicator = VoiceStatusIndicator(
            voice_service=mock_voice_service
        )
        
        # Act
        rendered = indicator.render()
        
        # Assert
        assert "status" in rendered.lower()
        assert "idle" in rendered.lower()  # Default state

    def test_voice_status_indicator_update(self, mock_voice_service):
        """Test voice status indicator state update."""
        # Arrange
        from src.ui.voice_components import VoiceStatusIndicator
        
        indicator = VoiceStatusIndicator(
            voice_service=mock_voice_service
        )
        
        # Act
        mock_voice_service.state = "LISTENING"
        rendered = indicator.render()
        
        # Assert
        assert "listening" in rendered.lower()