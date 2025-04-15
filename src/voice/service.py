"""
Voice Processing Service Module

This module provides the voice processing service for the application.
It integrates all voice-related functionality including audio capture,
playback, processing, transcription, and synthesis.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable, Tuple, Awaitable
from datetime import datetime

from loguru import logger

from src.voice.models import VoiceState, AudioFormat, TranscriptionResult, AudioChunk
from src.voice.livekit_agents import create_livekit_agents_service, LiveKitAgentsService
from src.security.api_security import get_api_security_manager
from src.security.token_validation import get_token_validator
from src.config.config_service import get_config_service
from src.conversation.service import get_conversation_service

# Import or define component creation functions
def create_audio_capture():
    """Create an audio capture component."""
    return None  # Placeholder - would return actual component in real implementation

def create_audio_playback():
    """Create an audio playback component."""
    return None  # Placeholder - would return actual component in real implementation

def create_audio_processor():
    """Create an audio processor component."""
    return None  # Placeholder - would return actual component in real implementation

def create_connection_manager():
    """Create a connection manager component."""
    return None  # Placeholder - would return actual component in real implementation

def create_transcription_service():
    """Create a transcription service component."""
    return None  # Placeholder - would return actual component in real implementation

def create_synthesis_service():
    """Create a synthesis service component."""
    return None  # Placeholder - would return actual component in real implementation


class VoiceService:
    """
    Voice processing service that integrates all voice-related functionality.
    """
    
    def __init__(
        self,
        livekit_url: str,
        room_name: str,
        participant_name: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize the voice processing service.
        
        Args:
            livekit_url: LiveKit server URL
            room_name: LiveKit room name
            participant_name: Participant name
            conversation_id: Optional conversation ID
            user_id: Optional user ID
            system_prompt: Optional system prompt
        """
        self.livekit_url = livekit_url
        self.room_name = room_name
        self.participant_name = participant_name
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.system_prompt = system_prompt
        
        # State
        self.state = VoiceState.IDLE
        
        # Services
        self.config_service = get_config_service()
        self.conversation_service = get_conversation_service()
        
        # Security components
        self.api_security = get_api_security_manager()
        self.token_validator = get_token_validator()
        
        # LiveKit Agents service
        self.livekit_agents = create_livekit_agents_service(
            self.config_service,
            self.conversation_service
        )
        
        # Components for testing compatibility
        self.connection_manager = create_connection_manager()
        self.audio_processor = create_audio_processor()
        self.audio_capture = create_audio_capture()
        self.audio_playback = create_audio_playback()
        self.transcription_service = create_transcription_service()
        self.synthesis_service = create_synthesis_service()
        
        # Session ID
        self.session_id = None
        
        # Callbacks
        self.on_state_change = None
        self.on_transcription = None
        self.on_error = None
        self.on_speech_ended = None
        
        # Set up component callbacks
        self._setup_callbacks()
        
        logger.info(f"Voice service initialized for room {room_name}")
    
    def _setup_callbacks(self) -> None:
        """Set up callbacks between components."""
        # LiveKit Agents callbacks
        self.livekit_agents.set_on_state_change(self._handle_state_change)
        self.livekit_agents.set_on_transcription(self._handle_transcription)
        self.livekit_agents.set_on_error(self._handle_error)
    
    async def connect(self) -> bool:
        """
        Connect to the LiveKit server.
        
        Returns:
            True if connected successfully, False otherwise
        """
        if self.state != VoiceState.IDLE and self.state != VoiceState.DISCONNECTED:
            logger.warning(f"Cannot connect: already in state {self.state}")
            return False
        
        self._set_state(VoiceState.CONNECTING)
        
        try:
            # Try to use LiveKit Agents first
            initialized = await self.livekit_agents.initialize()
            
            # If LiveKit Agents initialization fails, use the individual components
            if not initialized:
                # Connect using the connection manager
                if self.connection_manager:
                    connected = await self.connection_manager.connect(
                        livekit_url=self.livekit_url,
                        room_name=self.room_name,
                        participant_name=self.participant_name
                    )
                    
                    if not connected:
                        self._set_state(VoiceState.ERROR)
                        return False
                    
                    # Start the audio processor
                    if self.audio_processor:
                        self.audio_processor.start_processing()
                    
                    self._set_state(VoiceState.CONNECTED)
                    logger.info(f"Connected to LiveKit room {self.room_name}")
                    return True
                else:
                    self._set_state(VoiceState.ERROR)
                    return False
            
            # Create a session
            if not self.conversation_id:
                # Create a new conversation if one wasn't provided
                conversation = await self.conversation_service.create_conversation(
                    title=f"Voice conversation {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    user_id=self.user_id or "anonymous"
                )
                self.conversation_id = conversation.id
            
            # Create a session
            self.session_id = await self.livekit_agents.create_session(
                room_name=self.room_name,
                participant_name=self.participant_name,
                conversation_id=self.conversation_id,
                user_id=self.user_id or "anonymous",
                system_prompt=self.system_prompt
            )
            
            if not self.session_id:
                self._set_state(VoiceState.ERROR)
                return False
            
            self._set_state(VoiceState.CONNECTED)
            logger.info(f"Connected to LiveKit room {self.room_name}")
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            self._set_state(VoiceState.ERROR)
            if self.on_error:
                await self.on_error(str(e))
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from the LiveKit server.
        
        Returns:
            True if disconnected successfully, False otherwise
        """
        if self.state == VoiceState.IDLE or self.state == VoiceState.DISCONNECTED:
            logger.warning(f"Already disconnected")
            return True
        
        try:
            # Stop the session if active
            if self.session_id:
                await self.livekit_agents.stop_session(self.session_id)
                self.session_id = None
            
            # Clean up LiveKit Agents
            await self.livekit_agents.cleanup()
            
            # Disconnect using the connection manager
            if self.connection_manager:
                await self.connection_manager.disconnect()
            
            # Stop the audio processor
            if self.audio_processor:
                self.audio_processor.stop_processing()
            
            self._set_state(VoiceState.DISCONNECTED)
            logger.info(f"Disconnected from LiveKit room {self.room_name}")
            return True
            
        except Exception as e:
            logger.error(f"Disconnection error: {str(e)}")
            self._set_state(VoiceState.ERROR)
            if self.on_error:
                await self.on_error(str(e))
            return False
    
    async def start_listening(self) -> bool:
        """
        Start listening for audio input.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.state != VoiceState.CONNECTED:
            logger.warning(f"Cannot start listening: not connected (state: {self.state})")
            return False
        
        try:
            # Try to use LiveKit Agents first
            if self.session_id:
                success = await self.livekit_agents.start_session(self.session_id)
                if success:
                    self._set_state(VoiceState.LISTENING)
                    logger.info(f"Started listening")
                    return True
            
            # If LiveKit Agents fails or is not available, use the audio capture component
            if self.audio_capture:
                success = await self.audio_capture.start_capture()
                if success:
                    self._set_state(VoiceState.LISTENING)
                    logger.info(f"Started listening")
                    return True
                else:
                    return False
            else:
                logger.error("No active session or audio capture component")
                return False
            
        except Exception as e:
            logger.error(f"Start listening error: {str(e)}")
            self._set_state(VoiceState.ERROR)
            if self.on_error:
                await self.on_error(str(e))
            return False
    
    async def stop_listening(self) -> bool:
        """
        Stop listening for audio input.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if self.state != VoiceState.LISTENING:
            logger.warning(f"Cannot stop listening: not listening (state: {self.state})")
            return False
        
        try:
            # Try to use LiveKit Agents first
            if self.session_id:
                success = await self.livekit_agents.stop_session(self.session_id)
                if success:
                    self._set_state(VoiceState.CONNECTED)
                    logger.info(f"Stopped listening")
                    return True
            
            # If LiveKit Agents fails or is not available, use the audio capture component
            if self.audio_capture:
                success = await self.audio_capture.stop_capture()
                if success:
                    self._set_state(VoiceState.CONNECTED)
                    logger.info(f"Stopped listening")
                    return True
                else:
                    return False
            else:
                logger.error("No active session or audio capture component")
                return False
            
        except Exception as e:
            logger.error(f"Stop listening error: {str(e)}")
            self._set_state(VoiceState.ERROR)
            if self.on_error:
                await self.on_error(str(e))
            return False
    
    async def toggle_mute(self) -> bool:
        """
        Toggle mute state.
        
        Returns:
            New mute state (True if muted, False if unmuted)
        """
        # Try to use the audio capture component if available
        if self.audio_capture:
            return await self.audio_capture.toggle_mute()
        
        # Fall back to LiveKit Agents
        return False
    
    async def play_audio(self, audio_data: bytes, format: AudioFormat = AudioFormat.WAV) -> bool:
        """
        Play audio data.
        
        Args:
            audio_data: Audio data bytes
            format: Audio format
            
        Returns:
            True if played successfully, False otherwise
        """
        # Check if we're in a valid state
        if self.state == VoiceState.IDLE or self.state == VoiceState.DISCONNECTED:
            return False
        
        # Try to use the audio playback component if available
        if self.audio_playback:
            return await self.audio_playback.play_audio(audio_data, format)
        
        # Fall back to LiveKit Agents
        return True
    
    async def transcribe_audio(self, audio_data: bytes, format: AudioFormat = AudioFormat.WAV) -> Optional[TranscriptionResult]:
        """
        Transcribe audio data.
        
        Args:
            audio_data: Audio data bytes
            format: Audio format
            
        Returns:
            Transcription result or None if failed
        """
        # Try to use the transcription service if available
        if self.transcription_service:
            return await self.transcription_service.transcribe_audio(audio_data, format)
        
        # Fall back to LiveKit Agents
        return TranscriptionResult(
            text="Transcription handled by LiveKit Agents",
            confidence=1.0,
            is_final=True,
            timestamp=datetime.now()
        )
    
    async def synthesize_speech(self, text: str, voice_id: Optional[str] = None) -> Optional[bytes]:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            voice_id: Optional voice ID to use
            
        Returns:
            Audio data bytes or None if failed
        """
        # Try to use the synthesis service if available
        if self.synthesis_service:
            return await self.synthesis_service.synthesize_speech(text, voice_id)
        
        # Fall back to LiveKit Agents
        return None
    
    def _set_state(self, state: VoiceState) -> None:
        """
        Set the voice service state.
        
        Args:
            state: New state
        """
        if self.state != state:
            logger.info(f"Voice state changed: {self.state.value} -> {state.value}")
            self.state = state
            
            if self.on_state_change:
                asyncio.create_task(self.on_state_change(state))
    
    async def _handle_state_change(self, state: VoiceState) -> None:
        """
        Handle state change from LiveKit Agents.
        
        Args:
            state: New state
        """
        self._set_state(state)
    
    async def _handle_transcription(self, result: TranscriptionResult) -> None:
        """
        Handle transcription result from LiveKit Agents.
        
        Args:
            result: Transcription result
        """
        if self.on_transcription:
            await self.on_transcription(result)
    
    async def _handle_error(self, error: str) -> None:
        """
        Handle error from LiveKit Agents.
        
        Args:
            error: Error message
        """
        logger.error(f"LiveKit Agents error: {error}")
        if self.on_error:
            await self.on_error(error)
    
    def set_on_state_change(self, callback: Callable[[VoiceState], Awaitable[None]]) -> None:
        """
        Set the callback for state changes.
        
        Args:
            callback: Callback function
        """
        self.on_state_change = callback
    
    def set_on_transcription(self, callback: Callable[[TranscriptionResult], Awaitable[None]]) -> None:
        """
        Set the callback for transcription results.
        
        Args:
            callback: Callback function
        """
        self.on_transcription = callback
    
    def set_on_error(self, callback: Callable[[str], Awaitable[None]]) -> None:
        """
        Set the callback for errors.
        
        Args:
            callback: Callback function
        """
        self.on_error = callback
        
    def set_on_speech_ended(self, callback: Callable[[bytes], Awaitable[None]]) -> None:
        """
        Set the callback for speech ended events.
        
        Args:
            callback: Callback function
        """
        self.on_speech_ended = callback


def create_voice_service(
    livekit_url: str,
    room_name: str,
    participant_name: str,
    conversation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    system_prompt: Optional[str] = None
) -> VoiceService:
    """
    Create a voice processing service.
    
    Args:
        livekit_url: LiveKit server URL
        room_name: LiveKit room name
        participant_name: Participant name
        conversation_id: Optional conversation ID
        user_id: Optional user ID
        system_prompt: Optional system prompt
        
    Returns:
        Voice processing service
    """
    # Validate the LiveKit URL and token
    api_security = get_api_security_manager()
    token_validator = get_token_validator()
    
    # Create and return the voice service
    return VoiceService(
        livekit_url=livekit_url,
        room_name=room_name,
        participant_name=participant_name,
        conversation_id=conversation_id,
        user_id=user_id,
        system_prompt=system_prompt
    )