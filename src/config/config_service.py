"""
Configuration Service Module

This module provides a service for accessing validated configuration values
and managing secure secrets retrieval.
"""

import re
import os
from typing import Dict, Any, List, Optional, Union, TypeVar, Generic, Callable, Type, cast
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel, Field, validator, ValidationError

from src.security.secrets_manager import get_secrets_manager
from src.config.environment import Environment

# Type variable for generic validation
T = TypeVar('T')


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails."""
    pass


class ConfigValueType(Enum):
    """Enumeration of configuration value types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"


@dataclass
class ConfigValueSpec(Generic[T]):
    """
    Specification for a configuration value including validation rules.
    """
    key: str
    value_type: ConfigValueType
    required: bool = True
    default: Optional[T] = None
    description: str = ""
    secret: bool = False
    validator: Optional[Callable[[T], T]] = None
    options: Optional[List[T]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None

    def validate(self, value: Any) -> T:
        """
        Validate a configuration value against the specification.
        
        Args:
            value: The value to validate
            
        Returns:
            The validated value (possibly transformed)
            
        Raises:
            ConfigValidationError: If validation fails
        """
        if value is None:
            if self.required:
                raise ConfigValidationError(f"Required configuration value '{self.key}' is missing")
            return cast(T, self.default)
            
        # Type validation
        try:
            if self.value_type == ConfigValueType.STRING:
                validated_value = str(value)
            elif self.value_type == ConfigValueType.INTEGER:
                validated_value = int(value)
            elif self.value_type == ConfigValueType.FLOAT:
                validated_value = float(value)
            elif self.value_type == ConfigValueType.BOOLEAN:
                if isinstance(value, bool):
                    validated_value = value
                elif isinstance(value, str):
                    validated_value = value.lower() in ("true", "1", "yes", "y", "t")
                else:
                    validated_value = bool(value)
            elif self.value_type == ConfigValueType.LIST:
                if isinstance(value, list):
                    validated_value = value
                elif isinstance(value, str):
                    validated_value = [item.strip() for item in value.split(",")]
                else:
                    raise ConfigValidationError(f"Cannot convert {value} to list")
            elif self.value_type == ConfigValueType.DICT:
                if isinstance(value, dict):
                    validated_value = value
                else:
                    raise ConfigValidationError(f"Cannot convert {value} to dict")
            else:
                validated_value = value
        except (ValueError, TypeError) as e:
            raise ConfigValidationError(f"Invalid type for '{self.key}': {str(e)}")
            
        # Range validation for numeric types
        if self.value_type in (ConfigValueType.INTEGER, ConfigValueType.FLOAT):
            if self.min_value is not None and validated_value < self.min_value:
                raise ConfigValidationError(
                    f"Value for '{self.key}' ({validated_value}) is less than minimum ({self.min_value})"
                )
            if self.max_value is not None and validated_value > self.max_value:
                raise ConfigValidationError(
                    f"Value for '{self.key}' ({validated_value}) is greater than maximum ({self.max_value})"
                )
                
        # Pattern validation for strings
        if self.value_type == ConfigValueType.STRING and self.pattern:
            if not re.match(self.pattern, validated_value):
                raise ConfigValidationError(
                    f"Value for '{self.key}' does not match pattern '{self.pattern}'"
                )
                
        # Options validation
        if self.options is not None and validated_value not in self.options:
            raise ConfigValidationError(
                f"Value for '{self.key}' ({validated_value}) is not one of the allowed options: {self.options}"
            )
            
        # Custom validator
        if self.validator:
            try:
                validated_value = self.validator(validated_value)
            except Exception as e:
                raise ConfigValidationError(f"Custom validation failed for '{self.key}': {str(e)}")
                
        return cast(T, validated_value)


class ConfigService:
    """
    Service for accessing validated configuration values and managing secure secrets.
    """
    
    def __init__(self, environment: Environment):
        """
        Initialize the configuration service.
        
        Args:
            environment: Environment instance for accessing environment variables
        """
        self.environment = environment
        self.secrets_manager = get_secrets_manager()
        self._specs: Dict[str, ConfigValueSpec] = {}
        self._validated_cache: Dict[str, Any] = {}
        
        # Register standard configuration specs
        self._register_standard_specs()
        
    def _register_standard_specs(self) -> None:
        """Register standard configuration specifications."""
        """Register standard configuration specifications."""
        # Supabase Configuration
        self.register_spec(ConfigValueSpec(
            key="SUPABASE_URL",
            value_type=ConfigValueType.STRING,
            required=True,
            description="URL of the Supabase instance",
            pattern=r"^https?://.*$"
        ))
        self.register_spec(ConfigValueSpec(
            key="SUPABASE_ANON_KEY",
            value_type=ConfigValueType.STRING,
            required=True,
            description="Anonymous API key for Supabase",
            secret=True
        ))
        self.register_spec(ConfigValueSpec(
            key="SUPABASE_SERVICE_KEY",
            value_type=ConfigValueType.STRING,
            required=True,
            description="Service role API key for admin operations",
            secret=True
        ))
        
        # LiveKit Configuration
        self.register_spec(ConfigValueSpec(
            key="LIVEKIT_API_KEY",
            value_type=ConfigValueType.STRING,
            required=True,
            description="API key for LiveKit",
            secret=True
        ))
        self.register_spec(ConfigValueSpec(
            key="LIVEKIT_API_SECRET",
            value_type=ConfigValueType.STRING,
            required=True,
            description="API secret for LiveKit",
            secret=True
        ))
        self.register_spec(ConfigValueSpec(
            key="LIVEKIT_URL",
            value_type=ConfigValueType.STRING,
            required=True,
            description="URL of the LiveKit server",
            pattern=r"^wss?://.*$"
        ))
        
        # LiveKit Agents Configuration
        self.register_spec(ConfigValueSpec(
            key="DEEPGRAM_API_KEY",
            value_type=ConfigValueType.STRING,
            required=True,
            description="API key for Deepgram speech-to-text service",
            secret=True
        ))
        self.register_spec(ConfigValueSpec(
            key="OPENAI_API_KEY",
            value_type=ConfigValueType.STRING,
            required=True,
            description="API key for OpenAI language models",
            secret=True
        ))
        self.register_spec(ConfigValueSpec(
            key="OPENAI_ORGANIZATION",
            value_type=ConfigValueType.STRING,
            required=False,
            description="Organization ID for OpenAI"
        ))
        self.register_spec(ConfigValueSpec(
            key="CARTESIA_API_KEY",
            value_type=ConfigValueType.STRING,
            required=True,
            description="API key for Cartesia text-to-speech service",
            secret=True
        ))
        
        # AI Service Configuration
        self.register_spec(ConfigValueSpec(
            key="AI_API_KEY",
            value_type=ConfigValueType.STRING,
            required=True,
            description="API key for the language model service",
            secret=True
        ))
        self.register_spec(ConfigValueSpec(
            key="AI_API_URL",
            value_type=ConfigValueType.STRING,
            required=True,
            description="URL of the language model API",
            pattern=r"^https?://.*$"
        ))
        self.register_spec(ConfigValueSpec(
            key="AI_MODEL_NAME",
            value_type=ConfigValueType.STRING,
            required=True,
            description="Name of the language model to use"
        ))
        self.register_spec(ConfigValueSpec(
            key="STT_API_KEY",
            value_type=ConfigValueType.STRING,
            required=True,
            description="API key for speech-to-text service",
            secret=True
        ))
        self.register_spec(ConfigValueSpec(
            key="STT_API_URL",
            value_type=ConfigValueType.STRING,
            required=True,
            description="URL of the speech-to-text API",
            pattern=r"^https?://.*$"
        ))
        self.register_spec(ConfigValueSpec(
            key="TTS_API_KEY",
            value_type=ConfigValueType.STRING,
            required=True,
            description="API key for text-to-speech service",
            secret=True
        ))
        self.register_spec(ConfigValueSpec(
            key="TTS_API_URL",
            value_type=ConfigValueType.STRING,
            required=True,
            description="URL of the text-to-speech API",
            pattern=r"^https?://.*$"
        ))
        
        # Application Configuration
        self.register_spec(ConfigValueSpec(
            key="APP_ENV",
            value_type=ConfigValueType.STRING,
            required=False,
            default="development",
            description="Application environment",
            options=["development", "production", "testing"]
        ))
        self.register_spec(ConfigValueSpec(
            key="APP_DEBUG",
            value_type=ConfigValueType.BOOLEAN,
            required=False,
            default=False,
            description="Enable debug mode"
        ))
        self.register_spec(ConfigValueSpec(
            key="APP_PORT",
            value_type=ConfigValueType.INTEGER,
            required=False,
            default=8000,
            description="Port for the application to run on",
            min_value=1,
            max_value=65535
        ))
        self.register_spec(ConfigValueSpec(
            key="APP_SECRET_KEY",
            value_type=ConfigValueType.STRING,
            required=True,
            description="Secret key for session encryption",
            secret=True
        ))
        self.register_spec(ConfigValueSpec(
            key="APP_CORS_ORIGINS",
            value_type=ConfigValueType.LIST,
            required=False,
            default=["*"],
            description="Allowed CORS origins"
        ))
        
        # Storage Configuration
        self.register_spec(ConfigValueSpec(
            key="STORAGE_PROVIDER",
            value_type=ConfigValueType.STRING,
            required=False,
            default="supabase",
            description="Storage provider for audio files",
            options=["supabase", "s3", "local"]
        ))
        self.register_spec(ConfigValueSpec(
            key="S3_BUCKET_NAME",
            value_type=ConfigValueType.STRING,
            required=False,
            description="S3 bucket name (if using S3)"
        ))
        self.register_spec(ConfigValueSpec(
            key="S3_REGION",
            value_type=ConfigValueType.STRING,
            required=False,
            description="S3 region (if using S3)"
        ))
        self.register_spec(ConfigValueSpec(
            key="S3_ACCESS_KEY",
            value_type=ConfigValueType.STRING,
            required=False,
            description="S3 access key (if using S3)",
            secret=True
        ))
        self.register_spec(ConfigValueSpec(
            key="S3_SECRET_KEY",
            value_type=ConfigValueType.STRING,
            required=False,
            description="S3 secret key (if using S3)",
            secret=True
        ))
        self.register_spec(ConfigValueSpec(
            key="LOCAL_STORAGE_PATH",
            value_type=ConfigValueType.STRING,
            required=False,
            default="./storage",
            description="Path for local storage (if using local)"
        ))
        
        # Logging Configuration
        self.register_spec(ConfigValueSpec(
            key="LOG_LEVEL",
            value_type=ConfigValueType.STRING,
            required=False,
            default="info",
            description="Minimum log level",
            options=["debug", "info", "warning", "error", "critical"]
        ))
        self.register_spec(ConfigValueSpec(
            key="LOG_FORMAT",
            value_type=ConfigValueType.STRING,
            required=False,
            default="json",
            description="Log format",
            options=["json", "text"]
        ))
        self.register_spec(ConfigValueSpec(
            key="LOG_FILE",
            value_type=ConfigValueType.STRING,
            required=False,
            description="Log file path"
        ))
        
        # Secrets Manager Configuration
        self.register_spec(ConfigValueSpec(
            key="SECRETS_MASTER_KEY",
            value_type=ConfigValueType.STRING,
            required=False,
            description="Master key for secrets encryption",
            secret=True
        ))
        self.register_spec(ConfigValueSpec(
            key="SECRETS_DIR",
            value_type=ConfigValueType.STRING,
            required=False,
            description="Directory for storing encrypted secrets"
        ))
        
    def register_spec(self, spec: ConfigValueSpec) -> None:
        """
        Register a configuration value specification.
        
        Args:
            spec: Configuration value specification
        """
        self._specs[spec.key] = spec
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found or validation fails
            
        Returns:
            The configuration value
        """
        # Check if we have a cached validated value
        if key in self._validated_cache:
            return self._validated_cache[key]
            
        # Check if we have a spec for this key
        spec = self._specs.get(key)
        
        if spec:
            try:
                # Get the raw value (prioritizing secrets for sensitive values)
                if spec.secret:
                    raw_value = self.secrets_manager.get(key)
                    if raw_value is None:
                        raw_value = self.environment.get(key)
                else:
                    raw_value = self.environment.get(key)
                    
                # Validate the value
                validated_value = spec.validate(raw_value)
                
                # Cache the validated value
                self._validated_cache[key] = validated_value
                
                return validated_value
            except ConfigValidationError as e:
                if default is not None:
                    return default
                raise
        else:
            # No spec, just get the raw value
            return self.environment.get(key, default)
            
    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Get a boolean configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found or validation fails
            
        Returns:
            The boolean configuration value
        """
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "y", "t")
        return bool(value)
        
    def get_int(self, key: str, default: int = 0) -> int:
        """
        Get an integer configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found or validation fails
            
        Returns:
            The integer configuration value
        """
        value = self.get(key, default)
        if isinstance(value, int):
            return value
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
            
    def get_float(self, key: str, default: float = 0.0) -> float:
        """
        Get a float configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found or validation fails
            
        Returns:
            The float configuration value
        """
        value = self.get(key, default)
        if isinstance(value, float):
            return value
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
            
    def get_list(self, key: str, default: Optional[List[str]] = None, separator: str = ",") -> List[str]:
        """
        Get a list configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found or validation fails
            separator: Separator for string values
            
        Returns:
            The list configuration value
        """
        if default is None:
            default = []
            
        value = self.get(key)
        if value is None:
            return default
            
        if isinstance(value, list):
            return value
            
        if isinstance(value, str):
            return [item.strip() for item in value.split(separator)]
            
        return default
        
    def get_dict(self, key: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get a dictionary configuration value.
        
        Args:
            key: Configuration key
            default: Default value if not found or validation fails
            
        Returns:
            The dictionary configuration value
        """
        if default is None:
            default = {}
            
        value = self.get(key)
        if value is None:
            return default
            
        if isinstance(value, dict):
            return value
            
        return default
        
    def set(self, key: str, value: Any, secret: bool = False) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            secret: Whether this is a secret value
        """
        # Clear the cache for this key
        if key in self._validated_cache:
            del self._validated_cache[key]
            
        # If this is a secret, store it in the secrets manager
        if secret:
            self.secrets_manager.set(key, value)
        else:
            # For non-secrets, we can't actually set environment variables at runtime
            # But we can update our cache
            self._validated_cache[key] = value
            
    def validate_all_required(self) -> List[str]:
        """
        Validate all required configuration values.
        
        Returns:
            List of missing or invalid required configuration keys
        """
        missing_or_invalid = []
        
        for key, spec in self._specs.items():
            if spec.required:
                try:
                    self.get(key)
                except ConfigValidationError:
                    missing_or_invalid.append(key)
                    
        return missing_or_invalid
        
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
    def livekit_agents_config(self) -> Dict[str, Any]:
        """Get LiveKit Agents configuration."""
        return {
            "deepgram_api_key": self.get("DEEPGRAM_API_KEY"),
            "openai_api_key": self.get("OPENAI_API_KEY"),
            "openai_organization": self.get("OPENAI_ORGANIZATION"),
            "cartesia_api_key": self.get("CARTESIA_API_KEY"),
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
_config_service = None

def get_config_service() -> ConfigService:
    """
    Get the singleton ConfigService instance.
    
    Returns:
        ConfigService instance
    """
    global _config_service
    if _config_service is None:
        from src.config.environment import env
        _config_service = ConfigService(env)
    return _config_service