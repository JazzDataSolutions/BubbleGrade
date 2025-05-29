from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import wraps
import jwt
import time
from typing import Dict, List, Optional, Callable
import magic
import hashlib
from PIL import Image
import io

# File validation constants
ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/tiff', 'application/pdf'
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MIN_IMAGE_DIMENSIONS = (300, 300)  # Minimum width/height
MAX_IMAGE_DIMENSIONS = (4000, 4000)  # Maximum width/height

class FileValidator:
    @staticmethod
    def validate_file_type(file_content: bytes, filename: str) -> bool:
        """Validate file type using magic numbers (more secure than extension)"""
        try:
            mime_type = magic.from_buffer(file_content, mime=True)
            return mime_type in ALLOWED_MIME_TYPES
        except Exception:
            return False

    @staticmethod
    def validate_file_size(file_content: bytes) -> bool:
        """Validate file size"""
        return len(file_content) <= MAX_FILE_SIZE

    @staticmethod
    def validate_image_dimensions(file_content: bytes) -> tuple[bool, Optional[str]]:
        """Validate image dimensions and basic integrity"""
        try:
            # Skip PDF files
            mime_type = magic.from_buffer(file_content, mime=True)
            if mime_type == 'application/pdf':
                return True, None

            image = Image.open(io.BytesIO(file_content))
            width, height = image.size

            if width < MIN_IMAGE_DIMENSIONS[0] or height < MIN_IMAGE_DIMENSIONS[1]:
                return False, f"Image too small. Minimum dimensions: {MIN_IMAGE_DIMENSIONS[0]}x{MIN_IMAGE_DIMENSIONS[1]}"

            if width > MAX_IMAGE_DIMENSIONS[0] or height > MAX_IMAGE_DIMENSIONS[1]:
                return False, f"Image too large. Maximum dimensions: {MAX_IMAGE_DIMENSIONS[0]}x{MAX_IMAGE_DIMENSIONS[1]}"

            # Check for corruption
            image.verify()
            return True, None

        except Exception as e:
            return False, f"Invalid or corrupted image: {str(e)}"

    @staticmethod
    def calculate_file_hash(file_content: bytes) -> str:
        """Calculate SHA-256 hash for duplicate detection"""
        return hashlib.sha256(file_content).hexdigest()

    @classmethod
    def validate_upload(cls, file_content: bytes, filename: str) -> tuple[bool, Optional[str], Optional[str]]:
        """Complete file validation pipeline"""
        # Size validation
        if not cls.validate_file_size(file_content):
            return False, f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB", None

        # Type validation
        if not cls.validate_file_type(file_content, filename):
            return False, "Invalid file type. Only JPG, PNG, TIFF, and PDF files are allowed", None

        # Image dimension validation
        is_valid, error_msg = cls.validate_image_dimensions(file_content)
        if not is_valid:
            return False, error_msg, None

        # Calculate hash for duplicate detection
        file_hash = cls.calculate_file_hash(file_content)

        return True, None, file_hash


class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, List[float]] = {}
        self.limits = {
            'upload': {'requests': 10, 'window': 60},  # 10 uploads per minute
            'api': {'requests': 100, 'window': 60},    # 100 API calls per minute
            'export': {'requests': 20, 'window': 60}   # 20 exports per minute
        }

    def is_allowed(self, client_id: str, endpoint_type: str = 'api') -> tuple[bool, Optional[str]]:
        """Check if request is within rate limits"""
        now = time.time()
        limit_config = self.limits.get(endpoint_type, self.limits['api'])
        
        # Clean old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id] 
                if now - req_time < limit_config['window']
            ]
        else:
            self.requests[client_id] = []

        # Check if limit exceeded
        if len(self.requests[client_id]) >= limit_config['requests']:
            return False, f"Rate limit exceeded. Max {limit_config['requests']} requests per {limit_config['window']} seconds"

        # Add current request
        self.requests[client_id].append(now)
        return True, None


# Global rate limiter instance
rate_limiter = RateLimiter()

# JWT Security
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials) -> dict:
    """Verify JWT token and return user data"""
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token, 
            options={"verify_signature": False}  # In production, use proper secret
        )
        
        # Check expiration
        if payload.get('exp', 0) < time.time():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
            
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def get_client_id(request: Request) -> str:
    """Extract client identifier for rate limiting"""
    # Use IP address as fallback, could use user ID if authenticated
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def rate_limit(endpoint_type: str = 'api'):
    """Rate limiting decorator"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_id = get_client_id(request)
            allowed, error_msg = rate_limiter.is_allowed(client_id, endpoint_type)
            
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=error_msg
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_auth():
    """Authentication decorator"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract credentials from request
            # This would be injected by FastAPI dependency system
            return await func(*args, **kwargs)
        return wrapper
    return decorator