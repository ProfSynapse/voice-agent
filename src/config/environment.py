"""
Environment Configuration Module

This module handles loading and accessing environment variables for the application.
It follows a hierarchical approach to loading environment variables from different sources.
"""

import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from loguru import logger

class Environment:
    """
    Environment configuration manager that loads and provides access to environment variables.
    """
    
    def __init__(self):
        """Initialize the environment configuration."""
        self._load_environment_variables()
        self._validate_required_variables()
        
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
    
    def _validate_required_variables(self) -> None:
        """
        Validate that all required environment variables are set.
        Raises an exception if any required variable is missing.
        """
        required_variables = [
            # Supabase Configuration
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY",
            "SUPABASE_SERVICE_KEY",
            
            # LiveKit Configuration
            "LIVEKIT_API_KEY",
            "LIVEKIT_API_SECRET",
            "LIVEKIT_URL",
            
            # AI Service Configuration
            "AI_API_KEY",
            "AI_API_URL",
            "AI_MODEL_NAME",
            "STT_API_KEY",
            "STT_API_URL",
            "TTS_API_KEY",
            "TTS_API_URL",
            
            # Application Configuration
            "APP_SECRET_KEY",
        ]
        
        missing_variables = [var for var in required_variables if not os.environ.get(var)]
        
        if missing_variables:
            logger.error(f"Missing required environment variables: {', '.join(missing_variables)}")
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_variables)}")
    
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
    
    @property
    def is_development(self) -> bool:
        """Check if the application is running in development mode."""
        return self.get("APP_ENV", "development").lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if the application is running in production mode."""
        return self.get("APP_ENV", "development").lower() == "production"
    
    @property
    def is_testing(self) -> bool:
        """Check if the application is running in testing mode."""
        return self.get("APP_ENV", "development").lower() == "testing"
    
    @property
    def debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.get_bool("APP_DEBUG", self.is_development)
    
    @property
    def supabase_config(self) -> Dict[str, str]:
        """Get Supabase configuration."""
        return {
            "url": self.get("SUPABASE_URL"),
            "anon_key": self.get("SUPABASE_ANON_KEY"),
            "service_key": self.get("SUPABASE_SERVICE_KEY"),
        }
    
    @property
    def livekit_config(self) -> Dict[str, str]:
        """Get LiveKit configuration."""
        return {
            "api_key": self.get("LIVEKIT_API_KEY"),
            "api_secret": self.get("LIVEKIT_API_SECRET"),
            "url": self.get("LIVEKIT_URL"),
        }
    
    @property
    def ai_config(self) -> Dict[str, str]:
        """Get AI service configuration."""
        return {
            "api_key": self.get("AI_API_KEY"),
            "api_url": self.get("AI_API_URL"),
            "model_name": self.get("AI_MODEL_NAME"),
            "stt_api_key": self.get("STT_API_KEY"),
            "stt_api_url": self.get("STT_API_URL"),
            "tts_api_key": self.get("TTS_API_KEY"),
            "tts_api_url": self.get("TTS_API_URL"),
        }
    
    @property
    def app_config(self) -> Dict[str, Any]:
        """Get application configuration."""
        return {
            "env": self.get("APP_ENV", "development"),
            "debug": self.debug,
            "port": self.get_int("APP_PORT", 8000),
            "secret_key": self.get("APP_SECRET_KEY"),
            "cors_origins": self.get_list("APP_CORS_ORIGINS", ["*"]),
        }
    
    @property
    def storage_config(self) -> Dict[str, Any]:
        """Get storage configuration."""
        provider = self.get("STORAGE_PROVIDER", "supabase")
        
        config = {
            "provider": provider,
        }
        
        if provider == "s3":
            config.update({
                "bucket_name": self.get("S3_BUCKET_NAME"),
                "region": self.get("S3_REGION"),
                "access_key": self.get("S3_ACCESS_KEY"),
                "secret_key": self.get("S3_SECRET_KEY"),
            })
        elif provider == "local":
            config.update({
                "storage_path": self.get("LOCAL_STORAGE_PATH", "./storage"),
            })
            
        return config
    
    @property
    def logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            "level": self.get("LOG_LEVEL", "info").upper(),
            "format": self.get("LOG_FORMAT", "json"),
            "file": self.get("LOG_FILE"),
        }


# Create a singleton instance
env = Environment()