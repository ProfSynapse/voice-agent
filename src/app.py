"""
Main Application Module

This module initializes and runs the voice conversation agent application.
"""

import os
import asyncio
import logging
import sys
from typing import Dict, Any, Optional

import streamlit as st
from loguru import logger

from src.config import env
from src.auth.service import create_auth_service
from src.voice.service import create_voice_service
from src.conversation.service import create_conversation_service
from src.admin.service import create_admin_service
from src.storage.service import create_storage_service
from src.utils.supabase_client import create_supabase_client


class VoiceAgentApp:
    """
    Main application class for the Voice Conversation Agent.
    """
    
    def __init__(self):
        """Initialize the application."""
        self._configure_logging()
        self._initialize_services()
        
    def _configure_logging(self) -> None:
        """Configure application logging."""
        log_config = env.logging_config
        
        # Configure loguru
        logger.remove()  # Remove default handler
        
        # Add console handler
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
        
        logger.add(
            sink=sys.stderr, 
            format=log_format,
            level=log_config["level"],
            colorize=True
        )
        
        # Add file handler if specified
        if log_config.get("file"):
            logger.add(
                sink=log_config["file"],
                format=log_format if log_config["format"] == "text" else "{message}",
                level=log_config["level"],
                rotation="10 MB",
                retention="1 week",
                compression="zip",
                serialize=(log_config["format"] == "json")
            )
        
        # Intercept standard library logging
        class InterceptHandler(logging.Handler):
            def emit(self, record):
                # Get corresponding Loguru level if it exists
                try:
                    level = logger.level(record.levelname).name
                except ValueError:
                    level = record.levelno
                
                # Find caller from where originated the logged message
                frame, depth = logging.currentframe(), 2
                while frame.f_code.co_filename == logging.__file__:
                    frame = frame.f_back
                    depth += 1
                
                logger.opt(depth=depth, exception=record.exc_info).log(
                    level, record.getMessage()
                )
        
        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
        
        logger.info(f"Logging configured with level {log_config['level']}")
    
    def _initialize_services(self) -> None:
        """Initialize application services."""
        logger.info("Initializing application services")
        
        # Create Supabase client
        self.supabase = create_supabase_client(
            url=env.supabase_config["url"],
            anon_key=env.supabase_config["anon_key"],
            service_key=env.supabase_config["service_key"]
        )
        
        # Create storage service
        self.storage_service = create_storage_service(
            supabase=self.supabase,
            config=env.storage_config
        )
        
        # Create auth service
        self.auth_service = create_auth_service(
            supabase_client=self.supabase
        )
        
        # Create conversation service
        self.conversation_service = create_conversation_service(
            supabase_client=self.supabase,
            storage_service=self.storage_service
        )
        
        # Create admin service
        self.admin_service = create_admin_service(
            supabase_client=self.supabase,
            auth_service=self.auth_service
        )
        
        # Voice service will be created per conversation
        self.voice_service = None
        
        logger.info("Application services initialized")
    
    def create_voice_service(self, room_name: str, participant_name: str) -> None:
        """
        Create a voice service for a specific conversation.
        
        Args:
            room_name: Name of the LiveKit room (usually the conversation ID)
            participant_name: Name of the participant (usually the user ID)
        """
        self.voice_service = create_voice_service(
            livekit_url=env.livekit_config["url"],
            livekit_token=self._generate_livekit_token(room_name, participant_name),
            room_name=room_name,
            participant_name=participant_name
        )
    
    def _generate_livekit_token(self, room_name: str, participant_name: str) -> str:
        """
        Generate a LiveKit token for a participant in a room.
        
        Args:
            room_name: Name of the LiveKit room
            participant_name: Name of the participant
            
        Returns:
            Generated LiveKit token
        """
        from livekit import AccessToken
        
        token = AccessToken(
            api_key=env.livekit_config["api_key"],
            api_secret=env.livekit_config["api_secret"]
        )
        
        # Set token identity and metadata
        token.identity = participant_name
        token.name = participant_name
        
        # Add room permissions
        token.add_grant(
            room=room_name,
            room_join=True,
            room_publish=True,
            room_subscribe=True,
            can_publish=True,
            can_subscribe=True
        )
        
        return token.to_jwt()
    
    def run(self) -> None:
        """Run the Streamlit application."""
        from src.ui.app import run_ui
        
        # Run the UI with access to services
        run_ui(
            auth_service=self.auth_service,
            conversation_service=self.conversation_service,
            admin_service=self.admin_service,
            storage_service=self.storage_service,
            create_voice_service=self.create_voice_service
        )


def main():
    """Main entry point for the application."""
    import sys
    
    # Create and run the application
    app = VoiceAgentApp()
    app.run()


if __name__ == "__main__":
    main()