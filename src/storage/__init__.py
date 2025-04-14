"""
Storage Module

This module provides functionality for managing file storage.
"""

from src.storage.service import (
    StorageService,
    create_storage_service
)

__all__ = [
    'StorageService',
    'create_storage_service'
]