"""
Secure File Handler Module

This module provides secure file handling for the voice agent application.
It implements secure temporary file handling, randomized path components,
and proper cleanup mechanisms.
"""

import os
import logging
import tempfile
import shutil
import uuid
import time
from typing import Optional, Tuple, List, IO, Any
from pathlib import Path
import hashlib
import stat

from src.security.input_validation import get_input_validator

logger = logging.getLogger(__name__)


class SecureFileHandler:
    """Secure file handler for managing files securely."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the secure file handler.
        
        Args:
            base_dir: Base directory for file operations
        """
        self.validator = get_input_validator()
        
        # Set base directory for file operations
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Use a secure location for temporary files
            self.base_dir = Path(tempfile.gettempdir()) / "voice_agent"
            
        # Create the base directory if it doesn't exist
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Set secure permissions on the base directory
        os.chmod(self.base_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)  # 0o700
        
        # Keep track of temporary files for cleanup
        self.temp_files: List[Path] = []
        
    def create_temp_file(self, prefix: str = "", suffix: str = "") -> Tuple[Path, IO[bytes]]:
        """
        Create a secure temporary file.
        
        Args:
            prefix: Prefix for the filename
            suffix: Suffix for the filename
            
        Returns:
            Tuple of (file_path, file_object)
        """
        # Sanitize prefix and suffix
        prefix = self.validator.sanitize_filename(prefix)
        suffix = self.validator.sanitize_filename(suffix)
        
        # Add randomized component to the path
        random_dir = self._generate_random_path()
        temp_dir = self.base_dir / random_dir
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Set secure permissions on the directory
        os.chmod(temp_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)  # 0o700
        
        # Create a temporary file in the secure directory
        fd, temp_path = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=temp_dir)
        file_obj = os.fdopen(fd, "wb")
        
        # Add to the list of temporary files
        path_obj = Path(temp_path)
        self.temp_files.append(path_obj)
        
        return path_obj, file_obj
        
    def create_temp_directory(self, prefix: str = "") -> Path:
        """
        Create a secure temporary directory.
        
        Args:
            prefix: Prefix for the directory name
            
        Returns:
            Path to the temporary directory
        """
        # Sanitize prefix
        prefix = self.validator.sanitize_filename(prefix)
        
        # Add randomized component to the path
        random_dir = self._generate_random_path()
        parent_dir = self.base_dir / random_dir
        parent_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp(prefix=prefix, dir=parent_dir)
        
        # Set secure permissions on the directory
        os.chmod(temp_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)  # 0o700
        
        return Path(temp_dir)
        
    def save_uploaded_file(self, file_data: bytes, filename: str, directory: Optional[str] = None) -> Path:
        """
        Save an uploaded file securely.
        
        Args:
            file_data: File data
            filename: Original filename
            directory: Optional directory to save the file in
            
        Returns:
            Path to the saved file
        """
        # Sanitize the filename
        safe_filename = self.validator.sanitize_filename(filename)
        
        # Determine the directory to save the file in
        if directory:
            save_dir = Path(directory)
            save_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Create a secure temporary directory
            save_dir = self.create_temp_directory("upload_")
            
        # Generate a unique filename to avoid collisions
        name, ext = os.path.splitext(safe_filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        # Full path to the file
        file_path = save_dir / unique_filename
        
        # Write the file
        with open(file_path, "wb") as f:
            f.write(file_data)
            
        # Set secure permissions on the file
        os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)  # 0o600
        
        return file_path
        
    def secure_delete_file(self, file_path: Path) -> bool:
        """
        Securely delete a file by overwriting it before deletion.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not file_path.exists():
                return True
                
            # Get the file size
            file_size = file_path.stat().st_size
            
            # Overwrite the file with random data
            with open(file_path, "wb") as f:
                # Write random data in chunks
                chunk_size = 4096
                for _ in range(0, file_size, chunk_size):
                    f.write(os.urandom(min(chunk_size, file_size - f.tell())))
                    
            # Delete the file
            os.unlink(file_path)
            
            # Remove from the list of temporary files if present
            if file_path in self.temp_files:
                self.temp_files.remove(file_path)
                
            return True
        except Exception as e:
            logger.error(f"Error securely deleting file {file_path}: {str(e)}")
            return False
            
    def cleanup_temp_files(self, max_age: int = 3600) -> int:
        """
        Clean up temporary files older than max_age seconds.
        
        Args:
            max_age: Maximum age of files in seconds
            
        Returns:
            Number of files cleaned up
        """
        count = 0
        current_time = time.time()
        
        # Make a copy of the list to avoid modification during iteration
        temp_files_copy = self.temp_files.copy()
        
        for file_path in temp_files_copy:
            try:
                if not file_path.exists():
                    self.temp_files.remove(file_path)
                    continue
                    
                # Check the file age
                file_age = current_time - file_path.stat().st_mtime
                
                if file_age > max_age:
                    # Securely delete the file
                    if self.secure_delete_file(file_path):
                        count += 1
            except Exception as e:
                logger.error(f"Error cleaning up temporary file {file_path}: {str(e)}")
                
        return count
        
    def _generate_random_path(self) -> str:
        """
        Generate a randomized path component.
        
        Returns:
            Random path string
        """
        # Generate a UUID
        random_uuid = uuid.uuid4().hex
        
        # Create a path with multiple levels for additional security
        return f"{random_uuid[:2]}/{random_uuid[2:4]}/{random_uuid[4:]}"
        
    def compute_file_hash(self, file_path: Path, algorithm: str = "sha256") -> str:
        """
        Compute a hash of a file.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm to use
            
        Returns:
            File hash as a hexadecimal string
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, "rb") as f:
            # Read and update hash in chunks
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
                
        return hash_obj.hexdigest()
        
    def __del__(self):
        """Clean up temporary files when the object is destroyed."""
        self.cleanup_temp_files(0)  # Clean up all temporary files


# Create a singleton instance
_secure_file_handler = None

def get_secure_file_handler() -> SecureFileHandler:
    """
    Get the singleton SecureFileHandler instance.
    
    Returns:
        SecureFileHandler instance
    """
    global _secure_file_handler
    if _secure_file_handler is None:
        _secure_file_handler = SecureFileHandler()
    return _secure_file_handler