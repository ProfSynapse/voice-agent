"""
Voice UI Components Module

This module provides voice-specific UI components for the voice agent application.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Callable
import json

from loguru import logger

from src.ui.components import UIComponent, Container, Button, Icon, IconButton, Text, CircularProgress


class AudioWaveform(UIComponent):
    """Audio waveform component for visualizing audio."""
    
    def __init__(
        self, 
        id: str, 
        data: List[float] = None,
        color: str = "primary",
        height: int = 100,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an audio waveform component.
        
        Args:
            id: Component ID
            data: Waveform data points
            color: Waveform color
            height: Waveform height
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.data = data or []
        self.color = color
        self.height = height
        
    def render(self) -> Dict[str, Any]:
        """
        Render the audio waveform component as a dictionary.
        
        Returns:
            Audio waveform component representation as a dictionary
        """
        result = super().render()
        result.update({
            "data": self.data,
            "color": self.color,
            "height": self.height
        })
        return result


class VoiceButton(UIComponent):
    """Voice button component for voice interaction."""
    
    def __init__(
        self, 
        id: str, 
        is_listening: bool = False,
        is_processing: bool = False,
        size: str = "large",
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a voice button component.
        
        Args:
            id: Component ID
            is_listening: Whether the button is in listening state
            is_processing: Whether the button is in processing state
            size: Button size (small, medium, large)
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.is_listening = is_listening
        self.is_processing = is_processing
        self.size = size
        
    def render(self) -> Dict[str, Any]:
        """
        Render the voice button component as a dictionary.
        
        Returns:
            Voice button component representation as a dictionary
        """
        result = super().render()
        result.update({
            "is_listening": self.is_listening,
            "is_processing": self.is_processing,
            "size": self.size
        })
        return result


class ConversationBubble(UIComponent):
    """Conversation bubble component for displaying a conversation turn."""
    
    def __init__(
        self, 
        id: str, 
        text: str,
        role: str,
        timestamp: str,
        has_audio: bool = False,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a conversation bubble component.
        
        Args:
            id: Component ID
            text: Bubble text content
            role: Speaker role (user or assistant)
            timestamp: Message timestamp
            has_audio: Whether the message has audio
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.text = text
        self.role = role
        self.timestamp = timestamp
        self.has_audio = has_audio
        
    def render(self) -> Dict[str, Any]:
        """
        Render the conversation bubble component as a dictionary.
        
        Returns:
            Conversation bubble component representation as a dictionary
        """
        result = super().render()
        result.update({
            "text": self.text,
            "role": self.role,
            "timestamp": self.timestamp,
            "has_audio": self.has_audio
        })
        return result


class ConversationView(Container):
    """Conversation view component for displaying a conversation."""
    
    def __init__(
        self, 
        id: str, 
        title: str,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a conversation view component.
        
        Args:
            id: Component ID
            title: Conversation title
            styles: Optional styles for the component
        """
        super().__init__(id, styles=styles)
        self.title = title
        self.bubbles = []
        
    def add_bubble(
        self, 
        text: str, 
        role: str, 
        timestamp: str, 
        has_audio: bool = False
    ) -> 'ConversationView':
        """
        Add a conversation bubble.
        
        Args:
            text: Bubble text content
            role: Speaker role (user or assistant)
            timestamp: Message timestamp
            has_audio: Whether the message has audio
            
        Returns:
            Self for chaining
        """
        bubble_id = f"{self.id}_bubble_{len(self.bubbles)}"
        bubble = ConversationBubble(
            id=bubble_id,
            text=text,
            role=role,
            timestamp=timestamp,
            has_audio=has_audio
        )
        self.bubbles.append(bubble)
        self.add_child(bubble)
        return self
        
    def render(self) -> Dict[str, Any]:
        """
        Render the conversation view component as a dictionary.
        
        Returns:
            Conversation view component representation as a dictionary
        """
        result = super().render()
        result.update({
            "title": self.title,
            "bubbles": [bubble.render() for bubble in self.bubbles]
        })
        return result


class AudioPlayer(UIComponent):
    """Audio player component for playing audio."""
    
    def __init__(
        self, 
        id: str, 
        src: str,
        auto_play: bool = False,
        show_controls: bool = True,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an audio player component.
        
        Args:
            id: Component ID
            src: Audio source URL
            auto_play: Whether to auto-play the audio
            show_controls: Whether to show player controls
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.src = src
        self.auto_play = auto_play
        self.show_controls = show_controls
        
    def render(self) -> Dict[str, Any]:
        """
        Render the audio player component as a dictionary.
        
        Returns:
            Audio player component representation as a dictionary
        """
        result = super().render()
        result.update({
            "src": self.src,
            "auto_play": self.auto_play,
            "show_controls": self.show_controls
        })
        return result


class VoiceControls(Container):
    """Voice controls component for voice interaction controls."""
    
    def __init__(
        self, 
        id: str, 
        is_listening: bool = False,
        is_processing: bool = False,
        is_muted: bool = False,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize voice controls component.
        
        Args:
            id: Component ID
            is_listening: Whether the system is listening
            is_processing: Whether the system is processing
            is_muted: Whether the microphone is muted
            styles: Optional styles for the component
        """
        super().__init__(id, direction="row", align="center", justify="center", styles=styles)
        self.is_listening = is_listening
        self.is_processing = is_processing
        self.is_muted = is_muted
        
        # Create child components
        self._create_components()
        
    def _create_components(self):
        """Create the child components."""
        # Mute button
        mute_button = IconButton(
            id=f"{self.id}_mute",
            icon_name="mic_off" if self.is_muted else "mic",
            color="warning" if self.is_muted else "primary"
        )
        
        # Voice button
        voice_button = VoiceButton(
            id=f"{self.id}_voice",
            is_listening=self.is_listening,
            is_processing=self.is_processing,
            size="large"
        )
        
        # Status text
        status_text = Text(
            id=f"{self.id}_status",
            text=self._get_status_text(),
            variant="body2"
        )
        
        # Add components
        self.add_children([mute_button, voice_button, status_text])
        
    def _get_status_text(self) -> str:
        """Get the status text based on the current state."""
        if self.is_muted:
            return "Microphone is muted"
        elif self.is_listening:
            return "Listening..."
        elif self.is_processing:
            return "Processing..."
        else:
            return "Click to speak"
        
    def update_state(
        self, 
        is_listening: Optional[bool] = None,
        is_processing: Optional[bool] = None,
        is_muted: Optional[bool] = None
    ) -> 'VoiceControls':
        """
        Update the state of the voice controls.
        
        Args:
            is_listening: New listening state
            is_processing: New processing state
            is_muted: New muted state
            
        Returns:
            Self for chaining
        """
        if is_listening is not None:
            self.is_listening = is_listening
            
        if is_processing is not None:
            self.is_processing = is_processing
            
        if is_muted is not None:
            self.is_muted = is_muted
            
        # Recreate components with new state
        self.children = []
        self._create_components()
        
        return self
        
    def render(self) -> Dict[str, Any]:
        """
        Render the voice controls component as a dictionary.
        
        Returns:
            Voice controls component representation as a dictionary
        """
        result = super().render()
        result.update({
            "is_listening": self.is_listening,
            "is_processing": self.is_processing,
            "is_muted": self.is_muted
        })
        return result


class ConversationList(Container):
    """Conversation list component for displaying a list of conversations."""
    
    def __init__(
        self, 
        id: str, 
        selected_id: Optional[str] = None,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a conversation list component.
        
        Args:
            id: Component ID
            selected_id: ID of the selected conversation
            styles: Optional styles for the component
        """
        super().__init__(id, styles=styles)
        self.selected_id = selected_id
        self.conversations = []
        
    def add_conversation(
        self, 
        conversation_id: str,
        title: str,
        last_message: str,
        timestamp: str
    ) -> 'ConversationList':
        """
        Add a conversation to the list.
        
        Args:
            conversation_id: Conversation ID
            title: Conversation title
            last_message: Last message in the conversation
            timestamp: Conversation timestamp
            
        Returns:
            Self for chaining
        """
        self.conversations.append({
            "id": conversation_id,
            "title": title,
            "last_message": last_message,
            "timestamp": timestamp,
            "selected": conversation_id == self.selected_id
        })
        return self
        
    def render(self) -> Dict[str, Any]:
        """
        Render the conversation list component as a dictionary.
        
        Returns:
            Conversation list component representation as a dictionary
        """
        result = super().render()
        result.update({
            "selected_id": self.selected_id,
            "conversations": self.conversations
        })
        return result


class SystemPromptSelector(UIComponent):
    """System prompt selector component for selecting a system prompt."""
    
    def __init__(
        self, 
        id: str, 
        prompts: List[Dict[str, Any]],
        selected_id: Optional[str] = None,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a system prompt selector component.
        
        Args:
            id: Component ID
            prompts: List of prompts (each with id, name, category)
            selected_id: ID of the selected prompt
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.prompts = prompts
        self.selected_id = selected_id
        
    def render(self) -> Dict[str, Any]:
        """
        Render the system prompt selector component as a dictionary.
        
        Returns:
            System prompt selector component representation as a dictionary
        """
        result = super().render()
        result.update({
            "prompts": self.prompts,
            "selected_id": self.selected_id
        })
        return result


class VoiceSettings(Container):
    """Voice settings component for configuring voice settings."""
    
    def __init__(
        self, 
        id: str, 
        voice_enabled: bool = True,
        auto_play_responses: bool = True,
        voice_volume: int = 100,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a voice settings component.
        
        Args:
            id: Component ID
            voice_enabled: Whether voice is enabled
            auto_play_responses: Whether to auto-play responses
            voice_volume: Voice volume (0-100)
            styles: Optional styles for the component
        """
        super().__init__(id, styles=styles)
        self.voice_enabled = voice_enabled
        self.auto_play_responses = auto_play_responses
        self.voice_volume = voice_volume
        
    def render(self) -> Dict[str, Any]:
        """
        Render the voice settings component as a dictionary.
        
        Returns:
            Voice settings component representation as a dictionary
        """
        result = super().render()
        result.update({
            "voice_enabled": self.voice_enabled,
            "auto_play_responses": self.auto_play_responses,
            "voice_volume": self.voice_volume
        })
        return result


class MicrophoneButton(UIComponent):
    """Microphone button component for controlling voice input."""
    
    def __init__(
        self,
        id: str = "microphone-button",
        voice_service = None,
        on_click = None,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a microphone button component.
        
        Args:
            id: Component ID
            voice_service: Voice service instance
            on_click: Click event handler
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.voice_service = voice_service
        self.on_click = on_click
        
    async def handle_click(self):
        """Handle button click event."""
        if self.voice_service:
            if self.voice_service.state == "IDLE":
                await self.voice_service.connect()
            elif self.voice_service.state == "CONNECTED":
                await self.voice_service.start_listening()
            elif self.voice_service.state == "LISTENING":
                await self.voice_service.stop_listening()
        
        if self.on_click:
            self.on_click()
    
    def render(self) -> str:
        """
        Render the microphone button component as a string.
        
        Returns:
            Microphone button component representation as a string
        """
        state = "idle"
        if self.voice_service:
            state = self.voice_service.state.lower()
            
        return f"<button class='microphone-button {state}'>microphone</button>"


class MuteButton(UIComponent):
    """Mute button component for muting voice input."""
    
    def __init__(
        self,
        id: str = "mute-button",
        voice_service = None,
        on_click = None,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a mute button component.
        
        Args:
            id: Component ID
            voice_service: Voice service instance
            on_click: Click event handler
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.voice_service = voice_service
        self.on_click = on_click
        
    async def handle_click(self):
        """Handle button click event."""
        if self.voice_service:
            await self.voice_service.toggle_mute()
        
        if self.on_click:
            self.on_click()
    
    def render(self) -> str:
        """
        Render the mute button component as a string.
        
        Returns:
            Mute button component representation as a string
        """
        muted = self.voice_service and self.voice_service.is_muted
        state = "muted" if muted else "unmuted"
            
        return f"<button class='mute-button {state}'>mute</button>"


class VoiceStatusIndicator(UIComponent):
    """Voice status indicator component for displaying voice service status."""
    
    def __init__(
        self,
        id: str = "voice-status",
        voice_service = None,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a voice status indicator component.
        
        Args:
            id: Component ID
            voice_service: Voice service instance
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.voice_service = voice_service
        
    def render(self) -> str:
        """
        Render the voice status indicator component as a string.
        
        Returns:
            Voice status indicator component representation as a string
        """
        state = "idle"
        if self.voice_service:
            state = self.voice_service.state.lower()
            
        return f"<div class='voice-status status-{state}'>{state}</div>"


class VoiceWaveform(UIComponent):
    """Voice waveform component for visualizing voice input."""
    
    def __init__(
        self,
        id: str = "voice-waveform",
        data: List[float] = None,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a voice waveform component.
        
        Args:
            id: Component ID
            data: Waveform data points
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.data = data or []
        
    def render(self) -> str:
        """
        Render the voice waveform component as a string.
        
        Returns:
            Voice waveform component representation as a string
        """
        data_str = ",".join(str(d) for d in self.data)
        return f"<div class='voice-waveform' data-points='{data_str}'></div>"


class TranscriptDisplay(UIComponent):
    """Transcript display component for showing transcribed text."""
    
    def __init__(
        self,
        id: str = "transcript-display",
        text: str = "",
        is_final: bool = False,
        styles: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a transcript display component.
        
        Args:
            id: Component ID
            text: Transcribed text
            is_final: Whether the transcription is final
            styles: Optional styles for the component
        """
        super().__init__(id, styles)
        self.text = text
        self.is_final = is_final
        
    def render(self) -> str:
        """
        Render the transcript display component as a string.
        
        Returns:
            Transcript display component representation as a string
        """
        state = "final" if self.is_final else "interim"
        return f"<div class='transcript-display {state}'>{self.text}</div>"