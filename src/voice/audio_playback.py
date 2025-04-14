"""
Audio Playback Module

This module provides functionality for playing audio output.
"""

import os
import wave
import logging
import tempfile
from typing import Optional

import numpy as np
import sounddevice as sd
from pydub import AudioSegment
from loguru import logger

from src.voice.models import AudioFormat
from src.security.secure_file_handler import get_secure_file_handler

class AudioPlayback:
    """
    Audio playback handler for playing audio output.
    """
    
    def __init__(self):
        """Initialize the audio playback handler."""
        self.secure_file_handler = get_secure_file_handler()
        logger.info("Audio playback initialized")
    
    async def play_audio(self, audio_data: bytes, format: AudioFormat = AudioFormat.WAV) -> bool:
        """
        Play audio data.
        
        Args:
            audio_data: Audio data bytes
            format: Audio format
            
        Returns:
            True if played successfully, False otherwise
        """
        try:
            # Convert audio to playable format if needed
            if format != AudioFormat.WAV:
                # Create secure temporary files
                temp_in_path, temp_in_file = self.secure_file_handler.create_temp_file(
                    prefix="audio_in_", 
                    suffix=f".{format.value}"
                )
                
                temp_out_path, temp_out_file = self.secure_file_handler.create_temp_file(
                    prefix="audio_out_", 
                    suffix=".wav"
                )
                
                # Write input data
                temp_in_file.write(audio_data)
                temp_in_file.close()
                
                # Convert using pydub
                audio = AudioSegment.from_file(str(temp_in_path), format=format.value)
                audio.export(str(temp_out_path), format="wav")
                
                # Read converted audio
                with open(temp_out_path, 'rb') as f:
                    audio_data = f.read()
                
                # Clean up temp files securely
                self.secure_file_handler.secure_delete_file(temp_in_path)
                self.secure_file_handler.secure_delete_file(temp_out_path)
            
            # Create a secure temporary file for the WAV data
            temp_path, temp_file = self.secure_file_handler.create_temp_file(
                prefix="audio_play_", 
                suffix=".wav"
            )
            
            # Write the audio data
            temp_file.write(audio_data)
            temp_file.close()
            
            # Read WAV file properties
            with wave.open(str(temp_path), 'rb') as wav:
                channels = wav.getnchannels()
                sample_width = wav.getsampwidth()
                framerate = wav.getframerate()
                n_frames = wav.getnframes()
                audio_data = wav.readframes(n_frames)
            
            # Convert to numpy array
            dtype_map = {1: np.int8, 2: np.int16, 4: np.int32}
            audio_array = np.frombuffer(audio_data, dtype=dtype_map.get(sample_width, np.int16))
            
            if channels > 1:
                audio_array = audio_array.reshape(-1, channels)
            
            # Play audio
            sd.play(audio_array, framerate)
            sd.wait()
            
            # Clean up temp file securely
            self.secure_file_handler.secure_delete_file(temp_path)
            
            logger.info("Audio played successfully")
            return True
            
        except Exception as e:
            logger.error(f"Play audio error: {str(e)}")
            return False
    
    async def play_file(self, file_path: str) -> bool:
        """
        Play audio from a file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            True if played successfully, False otherwise
        """
        try:
            # Read the file
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            # Determine format from file extension
            _, ext = os.path.splitext(file_path)
            if ext.startswith('.'):
                ext = ext[1:]
            
            # Map extension to format
            format_map = {
                'wav': AudioFormat.WAV,
                'mp3': AudioFormat.MP3,
                'ogg': AudioFormat.OGG,
                'webm': AudioFormat.WEBM
            }
            
            format = format_map.get(ext.lower(), AudioFormat.WAV)
            
            # Play the audio
            return await self.play_audio(audio_data, format)
            
        except Exception as e:
            logger.error(f"Play file error: {str(e)}")
            return False


def create_audio_playback() -> AudioPlayback:
    """
    Create an audio playback handler.
    
    Returns:
        Audio playback handler
    """
    return AudioPlayback()