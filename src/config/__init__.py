"""
Configuration Package

This package provides configuration management for the application.
"""

from src.config.environment import env
from src.config.config_service import get_config_service, ConfigService

__all__ = ["env", "get_config_service", "ConfigService"]