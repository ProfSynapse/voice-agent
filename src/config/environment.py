"""
Environment Configuration Module

This module handles loading and accessing environment variables for the application.
It follows a hierarchical approach to loading environment variables from different sources.
"""

import os
import re
from typing import Dict, Any, List, Optional, Union, TypeVar, Generic, Callable, Type, cast
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv
from loguru import logger


class EnvironmentError(Exception):
    """Exception raised for environment configuration errors."""
    pass


class Environment:
    """
    Environment configuration manager that loads and provides access to environment variables.
    """
    
    def __init__(self):
        """Initialize the environment configuration."""
        self._load_environment_variables()
        
    def _load_environment_variables(self) -> None:
        """
        Load environment variables from various sources in order of precedence:
        1. Runtime environment variables
        2. .env.{APP_ENV}.local file
        3. .env.{APP_ENV} file
        4. .env.local file
        5. .env file
        """
        # Determine the environment (development, production, testing)
        app_env = os.environ.get("APP_ENV", "development")
        
        # Define the files to load in order of precedence (later files override earlier ones)
        dotenv_files = [
            ".env",
            ".env.local",
            f".env.{app_env}",
            f".env.{app_env}.local",
        ]
        
        # Load each file if it exists
        for dotenv_file in dotenv_files:
            if os.path.isfile(dotenv_file):
                logger.info(f"Loading environment variables from {dotenv_file}")
                load_dotenv(dotenv_file, override=True)
    @staticmethod
    def load(env_vars: Dict[str, str]) -> None:
        """
        Load environment variables from a dictionary.
        This is particularly useful for testing where you want to set specific
        environment variables without modifying actual environment files.
        
        Args:
            env_vars: Dictionary of environment variables to load
        """
        for key, value in env_vars.items():
            os.environ[key] = str(value)
            logger.debug(f"Set environment variable: {key}")
            
    def load_dict(self, env_vars: Dict[str, str]) -> None:
        """
        Instance method to load environment variables from a dictionary.
        This is particularly useful for testing where you want to set specific
        environment variables without modifying actual environment files.
        
        Args:
            env_vars: Dictionary of environment variables to load
        """
        Environment.load(env_vars)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get an environment variable.
        
        Args:
            key: The name of the environment variable
            default: Default value if the variable is not set
            
        Returns:
            The value of the environment variable or the default value
        """
        return os.environ.get(key, default)
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Get a boolean environment variable.
        
        Args:
            key: The name of the environment variable
            default: Default value if the variable is not set
            
        Returns:
            The boolean value of the environment variable
        """
        value = self.get(key, str(default)).lower()
        return value in ("true", "1", "yes", "y", "t")
    
    def get_int(self, key: str, default: int = 0) -> int:
        """
        Get an integer environment variable.
        
        Args:
            key: The name of the environment variable
            default: Default value if the variable is not set
            
        Returns:
            The integer value of the environment variable
        """
        try:
            return int(self.get(key, default))
        except ValueError:
            return default
    def get_float(self, key: str, default: float = 0.0) -> float:
        """
        Get a float environment variable.
        
        Args:
            key: The name of the environment variable
            default: Default value if the variable is not set
            
        Returns:
            The float value of the environment variable
        """
        try:
            return float(self.get(key, default))
        except ValueError:
            return default
    
    def get_list(self, key: str, default: Optional[List[str]] = None, separator: str = ",") -> List[str]:
        """
        Get a list environment variable by splitting a string.
        
        Args:
            key: The name of the environment variable
            default: Default value if the variable is not set
            separator: The separator to split the string
            
        Returns:
            The list value of the environment variable
        """
        if default is None:
            default = []
            
        value = self.get(key)
        if not value:
            return default
            
        return [item.strip() for item in value.split(separator)]


# Create a singleton instance
env = Environment()