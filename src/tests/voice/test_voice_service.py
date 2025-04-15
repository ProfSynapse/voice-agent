"""
Tests for the voice processing service.

This module contains tests for the voice processing service functionality.
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import MagicMock, patch, AsyncMock
import wave
import numpy as np
from datetime import datetime

from src.voice.service import VoiceService, create_voice_service
from src.voice.models import VoiceState, AudioFormat, TranscriptionResult, AudioChunk


class TestVoiceService:
    """Test suite for the VoiceService class."""

    @pytest.fixture
    def voice_service(self):
        """Create a voice service instance for testing."""
        service = VoiceService(
            livekit_url="wss://test-livekit-url.com",
            room_name="test-room",
            participant_name="test-participant"
        )
        return service

    @pytest.mark.asyncio
    async def test_connect_success(self, voice_service):
        """Test successful connection to LiveKit server."""
        # Arrange
        mock_websocket = AsyncMock()
        mock_connection_manager = MagicMock()
        mock_connection_manager.connect = AsyncMock(return_value=True)
        voice_service.connection_manager = mock_connection_manager
        
        # Act
        result = await voice_service.connect()
        
        # Assert
        assert result is True
        assert voice_service.state == VoiceState.CONNECTED
        mock_connection_manager.connect.assert_called_once_with(
            livekit_url="wss://test-livekit-url.com",
            room_name="test-room",
            participant_name="test-participant"
        )

    @pytest.mark.asyncio
    async def test_connect_failure(self, voice_service):
        """Test connection failure to LiveKit server."""
        # Arrange
        mock_connection_manager = MagicMock()
        mock_connection_manager.connect = AsyncMock(return_value=False)
        voice_service.connection_manager = mock_connection_manager
        
        # Act
        result = await voice_service.connect()
        
        # Assert
        assert result is False
        assert voice_service.state == VoiceState.ERROR

    @pytest.mark.asyncio
    async def test_disconnect(self, voice_service):
        """Test disconnection from LiveKit server."""
        # Arrange
        mock_connection_manager = MagicMock()
        mock_connection_manager.disconnect = AsyncMock(return_value=True)
        voice_service.connection_manager = mock_connection_manager
        
        mock_audio_processor = MagicMock()
        mock_audio_processor.stop_processing = MagicMock(return_value=True)
        voice_service.audio_processor = mock_audio_processor
        
        voice_service.state = VoiceState.CONNECTED
        
        # Act
        result = await voice_service.disconnect()
        
        # Assert
        assert result is True
        assert voice_service.state == VoiceState.DISCONNECTED
        mock_connection_manager.disconnect.assert_called_once()
        mock_audio_processor.stop_processing.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_listening(self, voice_service):
        """Test starting audio capture."""
        # Arrange
        voice_service.state = VoiceState.CONNECTED
        
        mock_audio_capture = MagicMock()
        mock_audio_capture.start_capture = AsyncMock(return_value=True)
        voice_service.audio_capture = mock_audio_capture
        
        # Act
        result = await voice_service.start_listening()
        
        # Assert
        assert result is True
        assert voice_service.state == VoiceState.LISTENING
        mock_audio_capture.start_capture.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_listening_not_connected(self, voice_service):
        """Test starting audio capture when not connected."""
        # Arrange
        voice_service.state = VoiceState.IDLE
        
        # Act
        result = await voice_service.start_listening()
        
        # Assert
        assert result is False
        assert voice_service.state == VoiceState.IDLE

    @pytest.mark.asyncio
    async def test_stop_listening(self, voice_service):
        """Test stopping audio capture."""
        # Arrange
        voice_service.state = VoiceState.LISTENING
        
        mock_audio_capture = MagicMock()
        mock_audio_capture.stop_capture = AsyncMock(return_value=True)
        voice_service.audio_capture = mock_audio_capture
        
        # Act
        result = await voice_service.stop_listening()
        
        # Assert
        assert result is True
        assert voice_service.state == VoiceState.CONNECTED
        mock_audio_capture.stop_capture.assert_called_once()

    @pytest.mark.asyncio
    async def test_toggle_mute(self, voice_service):
        """Test toggling mute state."""
        # Arrange
        mock_audio_capture = MagicMock()
        mock_audio_capture.toggle_mute = AsyncMock(side_effect=[True, False])
        voice_service.audio_capture = mock_audio_capture
        
        # Act
        result1 = await voice_service.toggle_mute()
        result2 = await voice_service.toggle_mute()
        
        # Assert
        assert result1 is True
        assert result2 is False
        assert mock_audio_capture.toggle_mute.call_count == 2

    @pytest.mark.asyncio
    async def test_play_audio_wav_format(self, voice_service):
        """Test playing audio in WAV format."""
        # Arrange
        voice_service.state = VoiceState.CONNECTED
        
        # Create a test WAV file
        sample_rate = 16000
        duration = 1  # seconds
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        audio_data = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16).tobytes()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
            with wave.open(temp.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data)
            
            # Read the WAV file
            with open(temp.name, 'rb') as f:
                wav_data = f.read()
            
            # Clean up
            temp_path = temp.name
        
        mock_audio_playback = MagicMock()
        mock_audio_playback.play_audio = AsyncMock(return_value=True)
        voice_service.audio_playback = mock_audio_playback
        
        # Act
        result = await voice_service.play_audio(wav_data, AudioFormat.WAV)
        
        # Assert
        assert result is True
        assert voice_service.state == VoiceState.CONNECTED  # Should return to previous state
        mock_audio_playback.play_audio.assert_called_once_with(wav_data, AudioFormat.WAV)
        
        # Clean up
        os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_play_audio_invalid_state(self, voice_service):
        """Test playing audio in an invalid state."""
        # Arrange
        voice_service.state = VoiceState.IDLE
        
        # Act
        result = await voice_service.play_audio(b'dummy data', AudioFormat.WAV)
        
        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_transcribe_audio(self, voice_service):
        """Test transcribing audio."""
        # Arrange
        # Create a test WAV file
        sample_rate = 16000
        duration = 1  # seconds
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        audio_data = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16).tobytes()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
            with wave.open(temp.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data)
            
            # Read the WAV file
            with open(temp.name, 'rb') as f:
                wav_data = f.read()
            
            # Clean up
            temp_path = temp.name
        
        # Create a mock transcription result
        mock_result = TranscriptionResult(
            text="Hello world",
            confidence=0.95,
            is_final=True,
            timestamp=datetime.now()
        )
        
        mock_transcription_service = MagicMock()
        mock_transcription_service.transcribe_audio = AsyncMock(return_value=mock_result)
        voice_service.transcription_service = mock_transcription_service
        
        # Act
        result = await voice_service.transcribe_audio(wav_data, AudioFormat.WAV)
        
        # Assert
        assert result is mock_result
        mock_transcription_service.transcribe_audio.assert_called_once_with(wav_data, AudioFormat.WAV)
        
        # Clean up
        os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_transcribe_audio_api_error(self, voice_service):
        """Test transcribing audio with API error."""
        # Arrange
        mock_transcription_service = MagicMock()
        mock_transcription_service.transcribe_audio = AsyncMock(return_value=None)
        voice_service.transcription_service = mock_transcription_service
        
        # Act
        result = await voice_service.transcribe_audio(b'dummy data', AudioFormat.WAV)
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_synthesize_speech(self, voice_service):
        """Test synthesizing speech from text."""
        # Arrange
        mock_audio_data = b'dummy audio data'
        
        mock_synthesis_service = MagicMock()
        mock_synthesis_service.synthesize_speech = AsyncMock(return_value=mock_audio_data)
        voice_service.synthesis_service = mock_synthesis_service
        
        # Act
        result = await voice_service.synthesize_speech("Hello world")
        
        # Assert
        assert result is mock_audio_data
        mock_synthesis_service.synthesize_speech.assert_called_once_with("Hello world", None)

    @pytest.mark.asyncio
    async def test_synthesize_speech_api_error(self, voice_service):
        """Test synthesizing speech with API error."""
        # Arrange
        mock_synthesis_service = MagicMock()
        mock_synthesis_service.synthesize_speech = AsyncMock(return_value=None)
        voice_service.synthesis_service = mock_synthesis_service
        
        # Act
        result = await voice_service.synthesize_speech("Hello world")
        
        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_set_state(self, voice_service):
        """Test setting the voice service state."""
        # Arrange
        callback = AsyncMock()
        voice_service.on_state_change = callback
        
        # Act
        with patch('asyncio.create_task') as mock_create_task:
            voice_service._set_state(VoiceState.CONNECTING)
            
            # Assert
            assert voice_service.state == VoiceState.CONNECTING
            mock_create_task.assert_called_once()

    def test_create_voice_service(self):
        """Test creating a voice service."""
        # Act
        service = create_voice_service(
            livekit_url="wss://test-livekit-url.com",
            room_name="test-room",
            participant_name="test-participant"
        )
        
        # Assert
        assert isinstance(service, VoiceService)
        assert service.livekit_url == "wss://test-livekit-url.com"
        assert service.room_name == "test-room"
        assert service.participant_name == "test-participant"