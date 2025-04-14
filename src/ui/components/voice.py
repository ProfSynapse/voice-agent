"""
Voice UI Components Module

This module provides voice-specific UI components for the voice agent application.
"""

from typing import Dict, List, Optional, Any, Callable

from src.ui.components.base import UIComponent
from src.ui.theme import get_ui_theme


class VoiceButton(UIComponent):
    """Voice button component for voice interactions."""
    
    def __init__(
        self, 
        id: str, 
        is_listening: bool = False,
        is_processing: bool = False,
        is_muted: bool = False,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a voice button component.
        
        Args:
            id: Component ID
            is_listening: Whether the button is in listening state
            is_processing: Whether the button is in processing state
            is_muted: Whether the button is muted
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.is_listening = is_listening
        self.is_processing = is_processing
        self.is_muted = is_muted
        
    def render(self) -> Dict[str, Any]:
        """
        Render the voice button component as a dictionary.
        
        Returns:
            Voice button component representation as a dictionary
        """
        theme = get_ui_theme()
        colors = theme.colors
        
        result = super().render()
        result.update({
            "is_listening": self.is_listening,
            "is_processing": self.is_processing,
            "is_muted": self.is_muted,
            "color": colors["primary"] if not self.is_muted else colors["error"]
        })
        return result


class VoiceWaveform(UIComponent):
    """Voice waveform component for visualizing audio."""
    
    def __init__(
        self, 
        id: str, 
        data: List[float] = None,
        color: str = None,
        height: int = 50,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a voice waveform component.
        
        Args:
            id: Component ID
            data: Waveform data points
            color: Waveform color
            height: Waveform height
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.data = data or []
        
        theme = get_ui_theme()
        self.color = color or theme.colors["primary"]
        self.height = height
        
    def render(self) -> Dict[str, Any]:
        """
        Render the voice waveform component as a dictionary.
        
        Returns:
            Voice waveform component representation as a dictionary
        """
        result = super().render()
        result.update({
            "data": self.data,
            "color": self.color,
            "height": self.height
        })
        return result


class VoiceIndicator(UIComponent):
    """Voice indicator component for showing voice activity."""
    
    def __init__(
        self, 
        id: str, 
        state: str = "idle",
        volume: float = 0.0,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a voice indicator component.
        
        Args:
            id: Component ID
            state: Indicator state (idle, listening, speaking, processing)
            volume: Current volume level (0.0 to 1.0)
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.state = state
        self.volume = max(0.0, min(1.0, volume))  # Clamp between 0 and 1
        
    def render(self) -> Dict[str, Any]:
        """
        Render the voice indicator component as a dictionary.
        
        Returns:
            Voice indicator component representation as a dictionary
        """
        theme = get_ui_theme()
        colors = theme.colors
        
        # Determine color based on state
        state_colors = {
            "idle": colors["textSecondary"],
            "listening": colors["primary"],
            "speaking": colors["info"],
            "processing": colors["warning"]
        }
        
        color = state_colors.get(self.state, colors["textSecondary"])
        
        result = super().render()
        result.update({
            "state": self.state,
            "volume": self.volume,
            "color": color
        })
        return result


class TranscriptDisplay(UIComponent):
    """Transcript display component for showing conversation transcripts."""
    
    def __init__(
        self, 
        id: str, 
        messages: List[Dict[str, Any]] = None,
        current_text: str = "",
        is_loading: bool = False,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a transcript display component.
        
        Args:
            id: Component ID
            messages: List of conversation messages
            current_text: Current text being transcribed
            is_loading: Whether the component is in loading state
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.messages = messages or []
        self.current_text = current_text
        self.is_loading = is_loading
        
    def add_message(
        self, 
        text: str, 
        sender: str = "user", 
        timestamp: Optional[str] = None
    ) -> 'TranscriptDisplay':
        """
        Add a message to the transcript.
        
        Args:
            text: Message text
            sender: Message sender (user or agent)
            timestamp: Message timestamp
            
        Returns:
            Self for chaining
        """
        self.messages.append({
            "text": text,
            "sender": sender,
            "timestamp": timestamp
        })
        return self
        
    def clear(self) -> 'TranscriptDisplay':
        """
        Clear the transcript.
        
        Returns:
            Self for chaining
        """
        self.messages = []
        self.current_text = ""
        return self
        
    def render(self) -> Dict[str, Any]:
        """
        Render the transcript display component as a dictionary.
        
        Returns:
            Transcript display component representation as a dictionary
        """
        result = super().render()
        result.update({
            "messages": self.messages,
            "current_text": self.current_text,
            "is_loading": self.is_loading
        })
        return result