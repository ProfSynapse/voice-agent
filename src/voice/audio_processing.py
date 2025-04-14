"""
Audio Processing Module

This module provides functionality for processing audio data, including
Voice Activity Detection (VAD) and audio format conversion.
"""

import os
import wave
import asyncio
import threading
import queue
import tempfile
from typing import Optional, List, Callable, Dict, Any
from datetime import datetime

import numpy as np
import webrtcvad
from loguru import logger

from src.voice.models import AudioChunk, AudioFormat
from src.security.secure_file_handler import get_secure_file_handler

class AudioProcessor:
    """
    Audio processor for handling audio data processing and voice activity detection.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        frame_duration_ms: int = 30,
        vad_aggressiveness: int = 3,
        silence_threshold: int = 10
    ):
        """
        Initialize the audio processor.
        
        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels
            frame_duration_ms: Frame duration in milliseconds
            vad_aggressiveness: VAD aggressiveness level (0-3)
            silence_threshold: Number of silent frames to consider speech ended
        """
        # Audio settings
        self.sample_rate = sample_rate
        self.channels = channels
        self.frame_duration_ms = frame_duration_ms
        
        # VAD settings
        self.vad = webrtcvad.Vad(vad_aggressiveness)
        self.silence_threshold = silence_threshold
        
        # Processing state
        self.is_processing = False
        self.processing_thread = None
        
        # Secure file handling
        self.secure_file_handler = get_secure_file_handler()
        
        # Callbacks
        self.on_speech_detected = None
        self.on_speech_ended = None
        self.on_error = None
        
        logger.info("Audio processor initialized")
    
    def start_processing(self, audio_queue: queue.Queue) -> bool:
        """
        Start processing audio data from the queue.
        
        Args:
            audio_queue: Queue of audio chunks to process
            
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_processing:
            logger.warning("Audio processing already started")
            return False
        
        try:
            # Start processing thread
            self.is_processing = True
            self.processing_thread = threading.Thread(
                target=self._process_audio_queue,
                args=(audio_queue,),
                daemon=True
            )
            self.processing_thread.start()
            
            logger.info("Started audio processing")
            return True
            
        except Exception as e:
            logger.error(f"Start processing error: {str(e)}")
            if self.on_error:
                self.on_error(str(e))
            return False
    
    def stop_processing(self) -> bool:
        """
        Stop processing audio data.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.is_processing:
            logger.warning("Audio processing not started")
            return False
        
        try:
            # Stop processing
            self.is_processing = False
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=2.0)
            
            logger.info("Stopped audio processing")
            return True
            
        except Exception as e:
            logger.error(f"Stop processing error: {str(e)}")
            if self.on_error:
                self.on_error(str(e))
            return False
    
    def set_on_speech_detected(self, callback: Callable[[List[bytes]], None]) -> None:
        """
        Set the callback for speech detection.
        
        Args:
            callback: Callback function that receives speech frames
        """
        self.on_speech_detected = callback
    
    def set_on_speech_ended(self, callback: Callable[[bytes], None]) -> None:
        """
        Set the callback for speech end detection.
        
        Args:
            callback: Callback function that receives WAV data
        """
        self.on_speech_ended = callback
    
    def set_on_error(self, callback: Callable[[str], None]) -> None:
        """
        Set the callback for errors.
        
        Args:
            callback: Callback function
        """
        self.on_error = callback
    
    def _process_audio_queue(self, audio_queue: queue.Queue) -> None:
        """
        Process audio data from the queue.
        
        Args:
            audio_queue: Queue of audio chunks to process
        """
        logger.info("Audio processing thread started")
        
        # Buffer for voice activity detection
        vad_buffer = []
        is_speech_active = False
        speech_frames = []
        silence_frame_count = 0
        
        while self.is_processing:
            try:
                # Get audio chunk from queue with timeout
                chunk = audio_queue.get(timeout=0.1)
                
                # Voice activity detection
                frame_data = chunk.data
                frame_size = len(frame_data)
                
                # Check if frame is valid for VAD
                if frame_size == int(self.sample_rate * self.frame_duration_ms / 1000 * 2):  # 16-bit samples
                    try:
                        is_speech = self.vad.is_speech(frame_data, self.sample_rate)
                        
                        # Add to VAD buffer
                        vad_buffer.append((frame_data, is_speech))
                        if len(vad_buffer) > 10:  # Keep last 10 frames
                            vad_buffer.pop(0)
                        
                        # Determine if speech is active based on buffer
                        speech_frames_in_buffer = sum(1 for _, is_speech in vad_buffer if is_speech)
                        buffer_speech_ratio = speech_frames_in_buffer / len(vad_buffer)
                        
                        # State machine for speech detection
                        if not is_speech_active and buffer_speech_ratio > 0.5:
                            # Speech started
                            is_speech_active = True
                            speech_frames = []
                            
                            # Add recent frames from buffer
                            for frame_data, _ in vad_buffer:
                                speech_frames.append(frame_data)
                            
                            logger.debug("Speech started")
                            
                            # Notify speech detection if callback is set
                            if self.on_speech_detected:
                                self.on_speech_detected(speech_frames.copy())
                            
                        if is_speech_active:
                            if is_speech:
                                # Continue speech
                                speech_frames.append(frame_data)
                                silence_frame_count = 0
                            else:
                                # Potential end of speech
                                speech_frames.append(frame_data)
                                silence_frame_count += 1
                                
                                if silence_frame_count >= self.silence_threshold:
                                    # Speech ended, process the audio
                                    logger.debug(f"Speech ended, processing {len(speech_frames)} frames")
                                    
                                    # Create WAV data from speech frames securely
                                    temp_path, temp_file = self.secure_file_handler.create_temp_file(
                                        prefix="speech_", 
                                        suffix=".wav"
                                    )
                                    temp_file.close()
                                    
                                    with wave.open(str(temp_path), 'wb') as wav:
                                        wav.setnchannels(self.channels)
                                        wav.setsampwidth(2)  # 16-bit
                                        wav.setframerate(self.sample_rate)
                                        for frame in speech_frames:
                                            wav.writeframes(frame)
                                    
                                    # Read the WAV file
                                    with open(temp_path, 'rb') as f:
                                        wav_data = f.read()
                                    
                                    # Notify speech ended if callback is set
                                    if self.on_speech_ended:
                                        self.on_speech_ended(wav_data)
                                    
                                    # Clean up temp file securely
                                    self.secure_file_handler.secure_delete_file(temp_path)
                                    
                                    # Reset state
                                    is_speech_active = False
                                    speech_frames = []
                                    silence_frame_count = 0
                    except Exception as e:
                        logger.error(f"VAD error: {str(e)}")
                
                # Mark task as done
                audio_queue.task_done()
                
            except queue.Empty:
                # No audio data in queue
                pass
            except Exception as e:
                logger.error(f"Audio processing error: {str(e)}")
                if self.on_error:
                    try:
                        asyncio.run_coroutine_threadsafe(
                            self.on_error(str(e)),
                            asyncio.get_event_loop()
                        )
                    except Exception as callback_error:
                        logger.error(f"Error calling error callback: {str(callback_error)}")
        
        logger.info("Audio processing thread stopped")


def create_audio_processor(
    sample_rate: int = 16000,
    channels: int = 1,
    frame_duration_ms: int = 30,
    vad_aggressiveness: int = 3,
    silence_threshold: int = 10
) -> AudioProcessor:
    """
    Create an audio processor.
    
    Args:
        sample_rate: Audio sample rate in Hz
        channels: Number of audio channels
        frame_duration_ms: Frame duration in milliseconds
        vad_aggressiveness: VAD aggressiveness level (0-3)
        silence_threshold: Number of silent frames to consider speech ended
        
    Returns:
        Audio processor
    """
    return AudioProcessor(
        sample_rate=sample_rate,
        channels=channels,
        frame_duration_ms=frame_duration_ms,
        vad_aggressiveness=vad_aggressiveness,
        silence_threshold=silence_threshold
    )