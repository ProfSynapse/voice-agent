"""
Voice Models Module

This module defines data models for the voice processing service.
"""

import enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field


class VoiceState(enum.Enum):
    """Voice service state."""
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    LISTENING = "listening"
    SPEAKING = "speaking"
    PROCESSING = "processing"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class AudioFormat(enum.Enum):
    """Audio format."""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    WEBM = "webm"
    PCM = "pcm"


@dataclass
class AudioChunk:
    """
    Audio chunk data.
    
    Attributes:
        data: Audio data bytes
        sample_rate: Sample rate in Hz
        channels: Number of channels
        dtype: Data type
        timestamp: Timestamp
    """
    data: bytes
    sample_rate: int
    channels: int
    dtype: str
    timestamp: Optional[float] = None


@dataclass
class TranscriptionResult:
    """
    Transcription result.
    
    Attributes:
        text: Transcribed text
        confidence: Confidence score (0-1)
        is_final: Whether this is a final result
        timestamp: Timestamp
        language: Detected language
        duration_ms: Audio duration in milliseconds
        segments: List of segments
        metadata: Additional metadata
    """
    text: str
    confidence: float
    is_final: bool
    timestamp: datetime
    language: Optional[str] = None
    duration_ms: Optional[int] = None
    segments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranscriptionResult':
        """
        Create a TranscriptionResult from a dictionary.
        
        Args:
            data: Dictionary data
            
        Returns:
            TranscriptionResult instance
        """
        return cls(
            text=data.get('text', ''),
            confidence=data.get('confidence', 0.0),
            is_final=data.get('is_final', True),
            timestamp=datetime.now(),
            language=data.get('language'),
            duration_ms=data.get('duration_ms'),
            segments=data.get('segments', []),
            metadata=data.get('metadata', {})
        )


@dataclass
class SynthesisVoice:
    """
    Speech synthesis voice.
    
    Attributes:
        id: Voice ID
        name: Voice name
        language: Voice language
        gender: Voice gender
        description: Voice description
        preview_url: URL to voice preview
        metadata: Additional metadata
    """
    id: str
    name: str
    language: str
    gender: str
    description: Optional[str] = None
    preview_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SynthesisVoice':
        """
        Create a SynthesisVoice from a dictionary.
        
        Args:
            data: Dictionary data
            
        Returns:
            SynthesisVoice instance
        """
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            language=data.get('language', ''),
            gender=data.get('gender', ''),
            description=data.get('description'),
            preview_url=data.get('preview_url'),
            metadata=data.get('metadata', {})
        )