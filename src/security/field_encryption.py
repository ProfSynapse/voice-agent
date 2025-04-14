"""
Field Encryption Module

This module provides field-level encryption for sensitive data in the voice agent application.
It allows encrypting and decrypting specific fields in data structures.
"""

import base64
import json
import logging
import os
from typing import Dict, Any, List, Union, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from src.security.secrets_manager import get_secrets_manager

logger = logging.getLogger(__name__)


class FieldEncryption:
    """Field-level encryption for sensitive data."""
    
    def __init__(self):
        """Initialize the field encryption."""
        self.secrets = get_secrets_manager()
        self.encryption_key = self._get_encryption_key()
        
    def _get_encryption_key(self) -> bytes:
        """
        Get the encryption key for field encryption.
        
        Returns:
            Encryption key bytes
        """
        # Get the field encryption key from secrets manager
        field_key = self.secrets.get("FIELD_ENCRYPTION_KEY")
        
        if not field_key:
            # Generate a new key if not found
            logger.info("Generating new field encryption key")
            field_key = Fernet.generate_key().decode()
            self.secrets.set("FIELD_ENCRYPTION_KEY", field_key)
            
        return field_key.encode()
        
    def encrypt_field(self, value: Any) -> str:
        """
        Encrypt a field value.
        
        Args:
            value: Value to encrypt
            
        Returns:
            Encrypted value as a string
        """
        if value is None:
            return None
            
        # Convert value to string if it's not already
        if not isinstance(value, str):
            value = json.dumps(value)
            
        fernet = Fernet(self.encryption_key)
        encrypted = fernet.encrypt(value.encode())
        return f"ENC:{base64.urlsafe_b64encode(encrypted).decode()}"
        
    def decrypt_field(self, encrypted_value: str) -> Any:
        """
        Decrypt a field value.
        
        Args:
            encrypted_value: Encrypted value as a string
            
        Returns:
            Decrypted value
        """
        if not encrypted_value or not isinstance(encrypted_value, str):
            return encrypted_value
            
        # Check if the value is encrypted
        if not encrypted_value.startswith("ENC:"):
            return encrypted_value
            
        try:
            # Remove the prefix
            encrypted_data = encrypted_value[4:]
            
            fernet = Fernet(self.encryption_key)
            decrypted = fernet.decrypt(base64.urlsafe_b64decode(encrypted_data))
            result = decrypted.decode()
            
            # Try to parse as JSON if it looks like JSON
            if result.startswith('{') or result.startswith('['):
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    pass
                    
            return result
        except Exception as e:
            logger.error(f"Error decrypting field: {str(e)}")
            return encrypted_value
            
    def encrypt_dict(self, data: Dict[str, Any], fields_to_encrypt: List[str]) -> Dict[str, Any]:
        """
        Encrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary to encrypt fields in
            fields_to_encrypt: List of field names to encrypt
            
        Returns:
            Dictionary with encrypted fields
        """
        if not data or not isinstance(data, dict):
            return data
            
        result = data.copy()
        
        for field in fields_to_encrypt:
            if field in result and result[field] is not None:
                result[field] = self.encrypt_field(result[field])
                
        return result
        
    def decrypt_dict(self, data: Dict[str, Any], fields_to_decrypt: List[str]) -> Dict[str, Any]:
        """
        Decrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary to decrypt fields in
            fields_to_decrypt: List of field names to decrypt
            
        Returns:
            Dictionary with decrypted fields
        """
        if not data or not isinstance(data, dict):
            return data
            
        result = data.copy()
        
        for field in fields_to_decrypt:
            if field in result and result[field] is not None:
                result[field] = self.decrypt_field(result[field])
                
        return result
        
    def encrypt_list(self, data_list: List[Dict[str, Any]], fields_to_encrypt: List[str]) -> List[Dict[str, Any]]:
        """
        Encrypt specific fields in a list of dictionaries.
        
        Args:
            data_list: List of dictionaries to encrypt fields in
            fields_to_encrypt: List of field names to encrypt
            
        Returns:
            List of dictionaries with encrypted fields
        """
        if not data_list or not isinstance(data_list, list):
            return data_list
            
        return [self.encrypt_dict(item, fields_to_encrypt) for item in data_list]
        
    def decrypt_list(self, data_list: List[Dict[str, Any]], fields_to_decrypt: List[str]) -> List[Dict[str, Any]]:
        """
        Decrypt specific fields in a list of dictionaries.
        
        Args:
            data_list: List of dictionaries to decrypt fields in
            fields_to_decrypt: List of field names to decrypt
            
        Returns:
            List of dictionaries with decrypted fields
        """
        if not data_list or not isinstance(data_list, list):
            return data_list
            
        return [self.decrypt_dict(item, fields_to_decrypt) for item in data_list]


# Create a singleton instance
_field_encryption = None

def get_field_encryption() -> FieldEncryption:
    """
    Get the singleton FieldEncryption instance.
    
    Returns:
        FieldEncryption instance
    """
    global _field_encryption
    if _field_encryption is None:
        _field_encryption = FieldEncryption()
    return _field_encryption