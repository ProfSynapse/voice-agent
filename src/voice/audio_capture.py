"""
Audio Capture Module

This module provides functionality for capturing audio input.
"""

import asyncio
import threading
import queue
import logging
from typing import Optional, Dict, Any, Callable

import numpy as np
import sounddevice as sd
from loguru import logger

from src.voice.models import AudioChunk, AudioFormat
from src.security.secure_file_handler import get_secure_file_handler

class AudioCapture:
    """
    Audio capture handler for capturing audio input.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        dtype: str = 'int16',
        block_size: int = 480,  # 30ms at 16kHz
        device: Optional[int] = None
    ):
        """
        Initialize the audio capture handler.
        
        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels
            dtype: Audio data type
            block_size: Audio block size in samples
            device: Audio device index
        """
        # Audio settings
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.block_size = block_size
        self.device = device
        
        # Stream state
        self.stream = None
        self.is_capturing = False
        self.is_muted = False
        
        # Audio queue
        self.audio_queue = queue.Queue()
        
        # Secure file handling
        self.secure_file_handler = get_secure_file_handler()
        
        # Callbacks
        self.on_error = None
        
        logger.info("Audio capture initialized")
    
    async def start_capture(self) -> bool:
        """
        Start capturing audio.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_capturing:
            logger.warning("Audio capture already started")
            return False
        
        try:
            # Create input stream
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype,
                blocksize=self.block_size,
                callback=self._audio_callback,
                device=self.device
            )
            
            # Start stream
            self.stream.start()
            self.is_capturing = True
            
            logger.info(f"Started audio capture (sample_rate={self.sample_rate}, channels={self.channels})")
            return True
            
        except Exception as e:
            logger.error(f"Start capture error: {str(e)}")
            if self.on_error:
                await self.on_error(str(e))
            return False
    
    async def stop_capture(self) -> bool:
        """
        Stop capturing audio.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.is_capturing:
            logger.warning("Audio capture not started")
            return False
        
        try:
            # Stop and close stream
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
            
            self.is_capturing = False
            
            logger.info("Stopped audio capture")
            return True
            
        except Exception as e:
            logger.error(f"Stop capture error: {str(e)}")
            if self.on_error:
                await self.on_error(str(e))
            return False
    
    async def toggle_mute(self) -> bool:
        """
        Toggle mute state.
        
        Returns:
            New mute state (True if muted, False if unmuted)
        """
        self.is_muted = not self.is_muted
        logger.info(f"Audio {'muted' if self.is_muted else 'unmuted'}")
        return self.is_muted
    
    def get_audio_queue(self) -> queue.Queue:
        """
        Get the audio queue.
        
        Returns:
            Audio queue
        """
        return self.audio_queue
    
    def _audio_callback(self, indata, frames, time, status) -> None:
        """
        Audio callback function for the sounddevice input stream.
        
        Args:
            indata: Input audio data
            frames: Number of frames
            time: Stream time
            status: Stream status
        """
        if status:
            logger.warning(f"Audio capture status: {status}")
        
        if self.is_muted:
            # Replace with silence if muted
            indata = np.zeros_like(indata)
        
        # Create audio chunk
        chunk = AudioChunk(
            data=indata.tobytes(),
            sample_rate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            timestamp=time.inputBufferAdcTime if time else None
        )
        
        # Add to queue
        self.audio_queue.put(chunk)
    
    def set_on_error(self, callback: Callable[[str], None]) -> None:
        """
        Set the callback for errors.
        
        Args:
            callback: Callback function
        """
        self.on_error = callback


def create_audio_capture(
    sample_rate: int = 16000,
    channels: int = 1,
    dtype: str = 'int16',
    block_size: int = 480,
    device: Optional[int] = None
) -> AudioCapture:
    """
    Create an audio capture handler.
    
    Args:
        sample_rate: Audio sample rate in Hz
        channels: Number of audio channels
        dtype: Audio data type
        block_size: Audio block size in samples
        device: Audio device index
        
    Returns:
        Audio capture handler
    """
    return AudioCapture(
        sample_rate=sample_rate,
        channels=channels,
        dtype=dtype,
        block_size=block_size,
        device=device
    )