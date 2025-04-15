"""
Storage Service Module

This module provides functionality for managing file storage.
"""

import os
import io
import uuid
import logging
from typing import Dict, List, Optional, Any, Union, BinaryIO

from loguru import logger


class StorageService:
    """Service for managing file storage."""
    
    def __init__(self, supabase, config):
        """
        Initialize the storage service.
        
        Args:
            supabase: Initialized Supabase client
            config: Storage configuration
        """
        self.supabase = supabase
        self.config = config
        self._ensure_buckets_exist()
    
    def _ensure_buckets_exist(self) -> None:
        """Ensure that required storage buckets exist."""
        try:
            # Get list of buckets
            buckets_response = self.supabase.storage.list_buckets().execute()
            existing_buckets = [bucket["name"] for bucket in buckets_response.data]
            
            # Create audio bucket if it doesn't exist
            if self.config["audio_bucket"] not in existing_buckets:
                logger.info(f"Creating audio bucket: {self.config['audio_bucket']}")
                self.supabase.storage.create_bucket(
                    self.config["audio_bucket"],
                    {"public": self.config["audio_public"]}
                ).execute()
            
            # Create user files bucket if it doesn't exist
            if self.config["files_bucket"] not in existing_buckets:
                logger.info(f"Creating files bucket: {self.config['files_bucket']}")
                self.supabase.storage.create_bucket(
                    self.config["files_bucket"],
                    {"public": self.config["files_public"]}
                ).execute()
                
            logger.info("Storage buckets verified")
        except Exception as e:
            logger.error(f"Error ensuring buckets exist: {str(e)}")
    
    async def upload_audio(
        self, 
        audio_data: Union[bytes, BinaryIO], 
        path: str
    ) -> Optional[str]:
        """
        Upload audio data to storage.
        
        Args:
            audio_data: Audio data as bytes or file-like object
            path: Storage path for the audio file
            
        Returns:
            Public URL of the uploaded audio or None if upload failed
        """
        try:
            # Ensure path has proper extension
            if not path.lower().endswith((".mp3", ".wav", ".ogg", ".m4a")):
                path = f"{path}.mp3"  # Default to mp3
            
            # Upload file
            response = self.supabase.storage.from_(
                self.config["audio_bucket"]
            ).upload(
                path=path,
                file=audio_data,
                file_options={"content-type": "audio/mpeg"}
            ).execute()
            
            if not response.data:
                logger.error(f"Failed to upload audio: {path}")
                return None
            
            # Get public URL
            url_response = self.supabase.storage.from_(
                self.config["audio_bucket"]
            ).get_public_url(path)
            
            return url_response
            
        except Exception as e:
            logger.error(f"Upload audio error: {str(e)}")
            return None
    
    async def delete_audio(self, path: str) -> bool:
        """
        Delete audio file from storage.
        
        Args:
            path: Storage path of the audio file
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            response = self.supabase.storage.from_(
                self.config["audio_bucket"]
            ).remove([path]).execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Delete audio error: {str(e)}")
            return False
    
    async def upload_file(
        self, 
        file_data: Union[bytes, BinaryIO], 
        path: str,
        content_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload a file to storage.
        
        Args:
            file_data: File data as bytes or file-like object
            path: Storage path for the file
            content_type: Optional content type
            
        Returns:
            Public URL of the uploaded file or None if upload failed
        """
        try:
            # Determine content type if not provided
            if content_type is None:
                ext = os.path.splitext(path)[1].lower()
                content_type = self._get_content_type(ext)
            
            # Upload file
            response = self.supabase.storage.from_(
                self.config["files_bucket"]
            ).upload(
                path=path,
                file=file_data,
                file_options={"content-type": content_type}
            ).execute()
            
            if not response.data:
                logger.error(f"Failed to upload file: {path}")
                return None
            
            # Get public URL
            url_response = self.supabase.storage.from_(
                self.config["files_bucket"]
            ).get_public_url(path)
            
            return url_response
            
        except Exception as e:
            logger.error(f"Upload file error: {str(e)}")
            return None
    
    async def delete_file(self, path: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            path: Storage path of the file
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            response = self.supabase.storage.from_(
                self.config["files_bucket"]
            ).remove([path]).execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Delete file error: {str(e)}")
            return False
    
    async def list_files(self, prefix: str) -> List[Dict[str, Any]]:
        """
        List files in storage with a given prefix.
        
        Args:
            prefix: Path prefix to list
            
        Returns:
            List of file objects
        """
        try:
            response = self.supabase.storage.from_(
                self.config["files_bucket"]
            ).list(prefix).execute()
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"List files error: {str(e)}")
            return []
    
    def _get_content_type(self, extension: str) -> str:
        """
        Get content type based on file extension.
        
        Args:
            extension: File extension (with dot)
            
        Returns:
            Content type string
        """
        content_types = {
            ".txt": "text/plain",
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".xml": "application/xml",
            ".pdf": "application/pdf",
            ".zip": "application/zip",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".mp4": "video/mp4",
            ".webm": "video/webm",
            ".ogg": "audio/ogg",
            ".m4a": "audio/m4a"
        }
        
        return content_types.get(extension, "application/octet-stream")


def create_storage_service(supabase, config):
    """
    Create and initialize the storage service.
    
    Args:
        supabase: Initialized Supabase client
        config: Storage configuration
        
    Returns:
        Initialized StorageService instance
    """
    return StorageService(supabase, config)


def get_storage_service():
    """
    Get the storage service.
    
    This is a wrapper around create_storage_service that gets the necessary
    dependencies and creates the service.
    
    Returns:
        Initialized StorageService instance
    """
    from src.utils.supabase_client import get_supabase_client
    from src.config.config_service import get_config_service
    
    supabase_client = get_supabase_client()
    config_service = get_config_service()
    
    # Get storage configuration
    storage_config = {
        "audio_bucket": "audio",
        "audio_public": True,
        "files_bucket": "files",
        "files_public": True
    }
    
    return create_storage_service(supabase_client, storage_config)