"""
Voice Processing Service Module

This module provides the voice processing service for the application.
It integrates all voice-related functionality including audio capture,
playback, processing, transcription, and synthesis.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable, Tuple
from datetime import datetime

from loguru import logger

from src.voice.models import VoiceState, AudioFormat, TranscriptionResult, AudioChunk
from src.voice.audio_capture import create_audio_capture, AudioCapture
from src.voice.audio_playback import create_audio_playback, AudioPlayback
from src.voice.audio_processing import create_audio_processor, AudioProcessor
from src.voice.connection import create_connection_manager, ConnectionManager
from src.voice.transcription import create_transcription_service, TranscriptionService
from src.voice.synthesis import create_synthesis_service, SynthesisService
from src.security.api_security import get_api_security_manager
from src.security.token_validation import get_token_validator


class VoiceService:
    """
    Voice processing service that integrates all voice-related functionality.
    """
    
    def __init__(
        self,
        livekit_url: str,
        room_name: str,
        participant_name: str
    ):
        """
        Initialize the voice processing service.
        
        Args:
            livekit_url: LiveKit server URL
            room_name: LiveKit room name
            participant_name: Participant name
        """
        self.livekit_url = livekit_url
        self.room_name = room_name
        self.participant_name = participant_name
        
        # State
        self.state = VoiceState.IDLE
        
        # Security components
        self.api_security = get_api_security_manager()
        self.token_validator = get_token_validator()
        
        # Voice components
        self.audio_capture = create_audio_capture()
        self.audio_playback = create_audio_playback()
        self.audio_processor = create_audio_processor()
        self.connection_manager = create_connection_manager()
        self.transcription_service = create_transcription_service()
        self.synthesis_service = create_synthesis_service()
        
        # Callbacks
        self.on_state_change = None
        self.on_transcription = None
        self.on_error = None
        
        # Set up component callbacks
        self._setup_callbacks()
        
        logger.info(f"Voice service initialized for room {room_name}")
    
    def _setup_callbacks(self) -> None:
        """Set up callbacks between components."""
        # Audio capture callbacks
        self.audio_capture.set_on_error(self._handle_error)
        
        # Audio processor callbacks
        self.audio_processor.set_on_speech_ended(self._handle_speech_ended)
        self.audio_processor.set_on_error(self._handle_error)
        
        # Connection callbacks
        self.connection_manager.set_on_error(self._handle_error)
    
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
            # Connect to LiveKit server
            connected = await self.connection_manager.connect(
                livekit_url=self.livekit_url,
                room_name=self.room_name,
                participant_name=self.participant_name
            )
            
            if not connected:
                self._set_state(VoiceState.ERROR)
                return False
            
            # Start audio processing
            self.audio_processor.start_processing(self.audio_capture.get_audio_queue())
            
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
            # Stop audio processing
            self.audio_processor.stop_processing()
            
            # Stop audio capture if active
            if self.state == VoiceState.LISTENING:
                await self.stop_listening()
            
            # Disconnect from LiveKit
            await self.connection_manager.disconnect()
            
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
            # Start audio capture
            success = await self.audio_capture.start_capture()
            if success:
                self._set_state(VoiceState.LISTENING)
                logger.info(f"Started listening")
                return True
            else:
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
            # Stop audio capture
            success = await self.audio_capture.stop_capture()
            if success:
                self._set_state(VoiceState.CONNECTED)
                logger.info(f"Stopped listening")
                return True
            else:
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
        return await self.audio_capture.toggle_mute()
    
    async def play_audio(self, audio_data: bytes, format: AudioFormat = AudioFormat.WAV) -> bool:
        """
        Play audio data.
        
        Args:
            audio_data: Audio data bytes
            format: Audio format
            
        Returns:
            True if played successfully, False otherwise
        """
        if self.state not in [VoiceState.CONNECTED, VoiceState.LISTENING]:
            logger.warning(f"Cannot play audio: not in correct state (state: {self.state})")
            return False
        
        previous_state = self.state
        self._set_state(VoiceState.SPEAKING)
        
        try:
            # Play audio
            success = await self.audio_playback.play_audio(audio_data, format)
            
            self._set_state(previous_state)
            return success
            
        except Exception as e:
            logger.error(f"Play audio error: {str(e)}")
            self._set_state(VoiceState.ERROR)
            if self.on_error:
                await self.on_error(str(e))
            return False
    
    async def transcribe_audio(self, audio_data: bytes, format: AudioFormat = AudioFormat.WAV) -> Optional[TranscriptionResult]:
        """
        Transcribe audio data.
        
        Args:
            audio_data: Audio data bytes
            format: Audio format
            
        Returns:
            Transcription result or None if failed
        """
        try:
            # Transcribe audio
            result = await self.transcription_service.transcribe_audio(audio_data, format)
            
            if result and self.on_transcription:
                await self.on_transcription(result)
            
            return result
                
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            if self.on_error:
                await self.on_error(str(e))
            return None
    
    async def synthesize_speech(self, text: str, voice_id: Optional[str] = None) -> Optional[bytes]:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            voice_id: Optional voice ID to use
            
        Returns:
            Audio data bytes or None if failed
        """
        try:
            # Synthesize speech
            audio_data = await self.synthesis_service.synthesize_speech(text, voice_id)
            return audio_data
                
        except Exception as e:
            logger.error(f"Speech synthesis error: {str(e)}")
            if self.on_error:
                await self.on_error(str(e))
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
    
    async def _handle_speech_ended(self, wav_data: bytes) -> None:
        """
        Handle speech ended event from audio processor.
        
        Args:
            wav_data: WAV audio data
        """
        # Send to LiveKit
        if self.connection_manager.is_connected():
            await self.connection_manager.send_audio(wav_data)
        
        # Transcribe audio
        await self.transcribe_audio(wav_data)
    
    async def _handle_error(self, error: str) -> None:
        """
        Handle error from any component.
        
        Args:
            error: Error message
        """
        logger.error(f"Component error: {error}")
        if self.on_error:
            await self.on_error(error)
    
    def set_on_state_change(self, callback: Callable[[VoiceState], None]) -> None:
        """
        Set the callback for state changes.
        
        Args:
            callback: Callback function
        """
        self.on_state_change = callback
    
    def set_on_transcription(self, callback: Callable[[TranscriptionResult], None]) -> None:
        """
        Set the callback for transcription results.
        
        Args:
            callback: Callback function
        """
        self.on_transcription = callback
    
    def set_on_error(self, callback: Callable[[str], None]) -> None:
        """
        Set the callback for errors.
        
        Args:
            callback: Callback function
        """
        self.on_error = callback


def create_voice_service(
    livekit_url: str,
    room_name: str,
    participant_name: str
) -> VoiceService:
    """
    Create a voice processing service.
    
    Args:
        livekit_url: LiveKit server URL
        room_name: LiveKit room name
        participant_name: Participant name
        
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
        participant_name=participant_name
    )