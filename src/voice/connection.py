"""
Connection Module

This module provides functionality for managing WebSocket connections
to the LiveKit server for voice communication.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable

import websockets
from loguru import logger

from src.voice.models import VoiceState
from src.security.api_security import get_api_security_manager
from src.security.token_validation import get_token_validator

class ConnectionManager:
    """
    Connection manager for handling WebSocket connections to the LiveKit server.
    """
    
    def __init__(self):
        """Initialize the connection manager."""
        self.websocket = None
        self.api_security = get_api_security_manager()
        self.token_validator = get_token_validator()
        
        # Callbacks
        self.on_message = None
        self.on_error = None
        
        logger.info("Connection manager initialized")
    
    async def connect(
        self,
        livekit_url: str,
        room_name: str,
        participant_name: str
    ) -> bool:
        """
        Connect to the LiveKit server.
        
        Args:
            livekit_url: LiveKit server URL
            room_name: LiveKit room name
            participant_name: Participant name
            
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            logger.info(f"Connecting to LiveKit server at {livekit_url}")
            
            # Generate a secure LiveKit token with minimal permissions
            livekit_token = self.api_security.create_livekit_token(
                room_name=room_name,
                participant_name=participant_name,
                ttl=3600,  # 1 hour
                can_publish=True,
                can_subscribe=True
            )
            
            # Create WebSocket connection with secure headers
            headers = {
                "Authorization": f"Bearer {livekit_token}"
            }
            
            # Add signed request headers for additional security
            signed_headers = self.api_security.sign_request(
                method="GET",
                url=livekit_url,
                headers=headers
            )
            
            self.websocket = await websockets.connect(
                livekit_url,
                extra_headers=signed_headers
            )
            
            # Send join message
            join_message = {
                "type": "join",
                "room": room_name,
                "participant": participant_name
            }
            
            await self.websocket.send(str(join_message))
            
            # Start message listener
            asyncio.create_task(self._listen_for_messages())
            
            logger.info(f"Connected to LiveKit room {room_name}")
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            if self.on_error:
                await self.on_error(str(e))
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect from the LiveKit server.
        
        Returns:
            True if disconnected successfully, False otherwise
        """
        try:
            # Close WebSocket connection
            if self.websocket:
                await self.websocket.close()
                self.websocket = None
            
            logger.info("Disconnected from LiveKit server")
            return True
            
        except Exception as e:
            logger.error(f"Disconnection error: {str(e)}")
            if self.on_error:
                await self.on_error(str(e))
            return False
    
    async def send_audio(self, audio_data: bytes) -> bool:
        """
        Send audio data to the LiveKit server.
        
        Args:
            audio_data: Audio data bytes
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.websocket or not self.websocket.open:
            logger.warning("Cannot send audio: not connected")
            return False
        
        try:
            await self.websocket.send(audio_data)
            return True
            
        except Exception as e:
            logger.error(f"Send audio error: {str(e)}")
            if self.on_error:
                await self.on_error(str(e))
            return False
    
    async def _listen_for_messages(self) -> None:
        """Listen for messages from the LiveKit server."""
        if not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                # Process message
                if self.on_message:
                    await self.on_message(message)
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
            
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            if self.on_error:
                await self.on_error(str(e))
    
    def set_on_message(self, callback: Callable[[Any], None]) -> None:
        """
        Set the callback for received messages.
        
        Args:
            callback: Callback function
        """
        self.on_message = callback
    
    def set_on_error(self, callback: Callable[[str], None]) -> None:
        """
        Set the callback for errors.
        
        Args:
            callback: Callback function
        """
        self.on_error = callback
    
    def is_connected(self) -> bool:
        """
        Check if the connection is active.
        
        Returns:
            True if connected, False otherwise
        """
        return self.websocket is not None and self.websocket.open


def create_connection_manager() -> ConnectionManager:
    """
    Create a connection manager.
    
    Returns:
        Connection manager
    """
    return ConnectionManager()