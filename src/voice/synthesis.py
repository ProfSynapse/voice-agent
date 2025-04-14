"""
Speech Synthesis Module

This module provides functionality for synthesizing text to speech.
"""

import logging
from typing import Optional, Dict, Any

import httpx
from loguru import logger

from src.voice.models import AudioFormat
from src.security.api_security import get_api_security_manager
from src.security.secrets_manager import get_secrets_manager
from src.security.field_encryption import get_field_encryption

class SynthesisService:
    """
    Speech synthesis service for converting text to audio.
    """
    
    def __init__(self):
        """Initialize the speech synthesis service."""
        self.api_security = get_api_security_manager()
        self.secrets = get_secrets_manager()
        self.field_encryption = get_field_encryption()
        logger.info("Speech synthesis service initialized")
    
    async def synthesize_speech(
        self, 
        text: str,
        voice_id: Optional[str] = None,
        output_format: AudioFormat = AudioFormat.WAV
    ) -> Optional[bytes]:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            voice_id: Optional voice ID to use
            output_format: Output audio format
            
        Returns:
            Audio data bytes or None if failed
        """
        try:
            # Get API configuration
            api_url = self.secrets.get("TTS_API_URL")
            if not api_url:
                logger.error("TTS_API_URL not found in secrets")
                return None
            
            # Get API key securely
            api_key = self.secrets.get("TTS_API_KEY")
            if not api_key:
                logger.error("TTS_API_KEY not found in secrets")
                return None
            
            # Encrypt sensitive data
            encrypted_text = self.field_encryption.encrypt_field(text)
            
            # Prepare request data
            data = {
                'text': encrypted_text,
                'output_format': output_format.value
            }
            
            # Add voice ID if provided
            if voice_id:
                data['voice_id'] = voice_id
            
            # Send text to TTS service with secure headers
            async with httpx.AsyncClient() as client:
                # Create secure headers with API key and request signing
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                    'X-Encryption-Enabled': 'true'  # Signal that content is encrypted
                }
                
                # Add signed request headers for additional security
                signed_headers = self.api_security.sign_request(
                    method="POST",
                    url=api_url,
                    data=data,
                    headers=headers
                )
                
                response = await client.post(
                    api_url,
                    json=data,
                    headers=signed_headers
                )
                
                if response.status_code == 200:
                    logger.info(f"Speech synthesis successful for text: {text[:30]}...")
                    return response.content
                else:
                    logger.error(f"TTS API error: {response.status_code} - {response.text}")
                    return None
                
        except Exception as e:
            logger.error(f"Speech synthesis error: {str(e)}")
            return None
    
    async def get_available_voices(self) -> Optional[Dict[str, Any]]:
        """
        Get available voices from the TTS service.
        
        Returns:
            Dictionary of available voices or None if failed
        """
        try:
            # Get API configuration
            api_url = self.secrets.get("TTS_API_URL")
            if not api_url:
                logger.error("TTS_API_URL not found in secrets")
                return None
            
            # Get API key securely
            api_key = self.secrets.get("TTS_API_KEY")
            if not api_key:
                logger.error("TTS_API_KEY not found in secrets")
                return None
            
            # Construct voices endpoint
            voices_url = f"{api_url}/voices"
            
            # Send request to get available voices
            async with httpx.AsyncClient() as client:
                # Create secure headers with API key and request signing
                headers = {
                    'Authorization': f'Bearer {api_key}'
                }
                
                # Add signed request headers for additional security
                signed_headers = self.api_security.sign_request(
                    method="GET",
                    url=voices_url,
                    headers=headers
                )
                
                response = await client.get(
                    voices_url,
                    headers=signed_headers
                )
                
                if response.status_code == 200:
                    voices_data = response.json()
                    logger.info(f"Retrieved {len(voices_data.get('voices', []))} available voices")
                    return voices_data
                else:
                    logger.error(f"Get voices API error: {response.status_code} - {response.text}")
                    return None
                
        except Exception as e:
            logger.error(f"Get voices error: {str(e)}")
            return None


def create_synthesis_service() -> SynthesisService:
    """
    Create a speech synthesis service.
    
    Returns:
        Speech synthesis service
    """
    return SynthesisService()