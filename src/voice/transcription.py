"""
Transcription Module

This module provides functionality for transcribing audio to text.
"""

import logging
from typing import Optional, Dict, Any

import httpx
from loguru import logger

from src.voice.models import AudioFormat, TranscriptionResult
from src.security.api_security import get_api_security_manager
from src.security.secrets_manager import get_secrets_manager
from src.security.secure_file_handler import get_secure_file_handler

class TranscriptionService:
    """
    Transcription service for converting audio to text.
    """
    
    def __init__(self):
        """Initialize the transcription service."""
        self.api_security = get_api_security_manager()
        self.secrets = get_secrets_manager()
        self.secure_file_handler = get_secure_file_handler()
        logger.info("Transcription service initialized")
    
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
            # Get API configuration
            api_url = self.secrets.get("STT_API_URL")
            if not api_url:
                logger.error("STT_API_URL not found in secrets")
                return None
            
            # Get API key securely
            api_key = self.secrets.get("STT_API_KEY")
            if not api_key:
                logger.error("STT_API_KEY not found in secrets")
                return None
            
            # Convert audio to WAV if needed
            if format != AudioFormat.WAV:
                audio_data = await self._convert_audio_format(audio_data, format, AudioFormat.WAV)
                if not audio_data:
                    return None
            
            # Send audio to transcription service with secure headers
            async with httpx.AsyncClient() as client:
                files = {'audio': ('audio.wav', audio_data, 'audio/wav')}
                
                # Create secure headers with API key and request signing
                headers = {
                    'Authorization': f'Bearer {api_key}'
                }
                
                # Add signed request headers for additional security
                signed_headers = self.api_security.sign_request(
                    method="POST",
                    url=api_url,
                    headers=headers
                )
                
                response = await client.post(
                    api_url,
                    files=files,
                    headers=signed_headers
                )
                
                if response.status_code == 200:
                    result_data = response.json()
                    
                    # Create transcription result
                    result = TranscriptionResult.from_dict(result_data)
                    
                    logger.info(f"Transcription successful: {result.text[:50]}...")
                    return result
                else:
                    logger.error(f"Transcription API error: {response.status_code} - {response.text}")
                    return None
                
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            return None
    
    async def _convert_audio_format(
        self, 
        audio_data: bytes, 
        input_format: AudioFormat, 
        output_format: AudioFormat
    ) -> Optional[bytes]:
        """
        Convert audio from one format to another.
        
        Args:
            audio_data: Audio data bytes
            input_format: Input audio format
            output_format: Output audio format
            
        Returns:
            Converted audio data bytes or None if failed
        """
        try:
            from pydub import AudioSegment
            
            # Create secure temporary files
            temp_in_path, temp_in_file = self.secure_file_handler.create_temp_file(
                prefix="transcribe_in_", 
                suffix=f".{input_format.value}"
            )
            
            temp_out_path, temp_out_file = self.secure_file_handler.create_temp_file(
                prefix="transcribe_out_", 
                suffix=f".{output_format.value}"
            )
            
            # Write input data
            temp_in_file.write(audio_data)
            temp_in_file.close()
            
            # Convert using pydub
            audio = AudioSegment.from_file(str(temp_in_path), format=input_format.value)
            audio.export(str(temp_out_path), format=output_format.value)
            
            # Read converted audio
            with open(temp_out_path, 'rb') as f:
                converted_data = f.read()
            
            # Clean up temp files securely
            self.secure_file_handler.secure_delete_file(temp_in_path)
            self.secure_file_handler.secure_delete_file(temp_out_path)
            
            return converted_data
            
        except Exception as e:
            logger.error(f"Audio conversion error: {str(e)}")
            return None


def create_transcription_service() -> TranscriptionService:
    """
    Create a transcription service.
    
    Returns:
        Transcription service
    """
    return TranscriptionService()