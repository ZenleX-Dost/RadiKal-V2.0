"""
Input validation utilities for file uploads and user input.

Provides secure validation for:
- File uploads (type, size, content)
- Image validation
- Input sanitization
- Path traversal prevention
"""

import os
import re
from typing import Optional, List, Tuple
from pathlib import Path
from fastapi import HTTPException, UploadFile, status
from PIL import Image
import io
import logging

# python-magic is optional
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

logger = logging.getLogger(__name__)


# Default configuration
DEFAULT_MAX_FILE_SIZE_MB = 10
DEFAULT_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
DEFAULT_ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png", 
    "image/gif",
    "image/bmp",
    "image/tiff",
    "image/webp"
}

# Magic bytes for common image formats
IMAGE_MAGIC_BYTES = {
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG\r\n\x1a\n': 'image/png',
    b'GIF87a': 'image/gif',
    b'GIF89a': 'image/gif',
    b'BM': 'image/bmp',
    b'II\x2a\x00': 'image/tiff',
    b'MM\x00\x2a': 'image/tiff',
    b'RIFF': 'image/webp',
}


class FileValidator:
    """Validates uploaded files for security."""
    
    def __init__(
        self,
        max_size_mb: float = DEFAULT_MAX_FILE_SIZE_MB,
        allowed_extensions: Optional[set] = None,
        allowed_content_types: Optional[set] = None,
    ):
        """
        Initialize file validator.
        
        Args:
            max_size_mb: Maximum file size in MB
            allowed_extensions: Set of allowed file extensions
            allowed_content_types: Set of allowed MIME types
        """
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.allowed_extensions = allowed_extensions or DEFAULT_ALLOWED_EXTENSIONS
        self.allowed_content_types = allowed_content_types or DEFAULT_ALLOWED_CONTENT_TYPES
    
    async def validate(self, file: UploadFile) -> Tuple[bytes, str]:
        """
        Validate uploaded file.
        
        Args:
            file: Uploaded file from FastAPI
            
        Returns:
            Tuple of (file_content, detected_content_type)
            
        Raises:
            HTTPException: If validation fails
        """
        # Validate filename
        self._validate_filename(file.filename)
        
        # Read content
        content = await file.read()
        await file.seek(0)  # Reset for potential re-read
        
        # Validate size
        self._validate_size(content, file.filename)
        
        # Validate content type by magic bytes
        detected_type = self._detect_content_type(content)
        self._validate_content_type(detected_type, file.filename)
        
        # Validate as image (can be opened by PIL)
        self._validate_image_content(content, file.filename)
        
        logger.info(f"File validated: {file.filename}, type={detected_type}, size={len(content)} bytes")
        
        return content, detected_type
    
    def _validate_filename(self, filename: Optional[str]) -> None:
        """Validate filename for security issues."""
        if not filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            logger.warning(f"Path traversal attempt detected: {filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename - path traversal not allowed"
            )
        
        # Check extension
        ext = Path(filename).suffix.lower()
        if ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed: {', '.join(self.allowed_extensions)}"
            )
        
        # Check for null bytes (bypass attempt)
        if '\x00' in filename:
            logger.warning(f"Null byte in filename detected: {repr(filename)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        
        # Check filename length
        if len(filename) > 255:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename too long (max 255 characters)"
            )
    
    def _validate_size(self, content: bytes, filename: str) -> None:
        """Validate file size."""
        if len(content) > self.max_size_bytes:
            max_mb = self.max_size_bytes / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {max_mb:.1f} MB"
            )
        
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file not allowed"
            )
    
    def _detect_content_type(self, content: bytes) -> str:
        """Detect content type from file magic bytes."""
        # Try magic bytes detection first
        for magic_bytes, content_type in IMAGE_MAGIC_BYTES.items():
            if content.startswith(magic_bytes):
                return content_type
        
        # Special case for WebP (has RIFF header)
        if content.startswith(b'RIFF') and b'WEBP' in content[:12]:
            return 'image/webp'
        
        # Fallback to python-magic if available
        if MAGIC_AVAILABLE:
            try:
                mime = magic.Magic(mime=True)
                return mime.from_buffer(content)
            except Exception:
                pass
        
        # Unknown type
        return "application/octet-stream"
    
    def _validate_content_type(self, content_type: str, filename: str) -> None:
        """Validate detected content type."""
        if content_type not in self.allowed_content_types:
            logger.warning(f"Invalid content type {content_type} for file {filename}")
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Content type not allowed: {content_type}"
            )
    
    def _validate_image_content(self, content: bytes, filename: str) -> None:
        """Validate that content is a valid image."""
        try:
            img = Image.open(io.BytesIO(content))
            img.verify()  # Verify image integrity
            
            # Re-open for actual validation (verify() closes the file)
            img = Image.open(io.BytesIO(content))
            
            # Check for reasonable dimensions
            width, height = img.size
            if width > 10000 or height > 10000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image dimensions too large (max 10000x10000)"
                )
            
            if width < 10 or height < 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image too small (min 10x10)"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Invalid image content in {filename}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file - could not process image"
            )


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing dangerous characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed"
    
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove null bytes
    filename = filename.replace('\x00', '')
    
    # Replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 200:
        name = name[:200]
    
    return f"{name}{ext}" if name else f"file{ext}"


def sanitize_string(value: str, max_length: int = 1000, allow_html: bool = False) -> str:
    """
    Sanitize user input string.
    
    Args:
        value: Input string
        max_length: Maximum allowed length
        allow_html: Whether to allow HTML tags
        
    Returns:
        Sanitized string
    """
    if not value:
        return ""
    
    # Truncate
    value = value[:max_length]
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Escape HTML if not allowed
    if not allow_html:
        value = (
            value
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#x27;')
        )
    
    return value


# Create default validator instance
file_validator = FileValidator()


async def validate_image_upload(file: UploadFile) -> Tuple[bytes, str]:
    """
    Convenience function to validate image upload.
    
    Args:
        file: Uploaded file
        
    Returns:
        Tuple of (content, content_type)
    """
    return await file_validator.validate(file)
