"""Authentication and authorization middleware for Makerkit integration."""

from typing import Optional, List, Callable
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


security = HTTPBearer()


class MakerkitAuth:
    """Makerkit JWT authentication handler."""
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        require_auth: bool = True
    ):
        """Initialize Makerkit authentication.
        
        Args:
            secret_key: Secret key for JWT validation.
            algorithm: JWT algorithm (default: HS256).
            require_auth: Whether authentication is required.
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.require_auth = require_auth
    
    def decode_token(self, token: str) -> dict:
        """Decode and validate JWT token.
        
        Args:
            token: JWT token string.
            
        Returns:
            Decoded token payload.
            
        Raises:
            HTTPException: If token is invalid or expired.
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            return payload
            
        except JWTError as e:
            logger.error(f"JWT validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
    
    def get_user_role(self, payload: dict) -> str:
        """Extract user role from token payload.
        
        Args:
            payload: Decoded token payload.
            
        Returns:
            User role string.
        """
        return payload.get("role", "operator")
    
    def verify_role(self, required_roles: List[str], user_role: str) -> bool:
        """Verify if user has required role.
        
        Args:
            required_roles: List of allowed roles.
            user_role: User's current role.
            
        Returns:
            True if user has required role.
        """
        return user_role in required_roles


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_handler: Optional[MakerkitAuth] = None
) -> dict:
    """Dependency to get current authenticated user.
    
    Args:
        credentials: HTTP bearer credentials.
        auth_handler: Authentication handler instance.
        
    Returns:
        User information from token.
    """
    if auth_handler is None:
        import os
        secret_key = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
        auth_handler = MakerkitAuth(secret_key=secret_key)
    
    token = credentials.credentials
    payload = auth_handler.decode_token(token)
    
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "role": auth_handler.get_user_role(payload),
        "payload": payload
    }


def require_role(allowed_roles: List[str]) -> Callable:
    """Decorator to require specific roles for endpoints.
    
    Args:
        allowed_roles: List of roles that can access the endpoint.
        
    Returns:
        Dependency function.
    """
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", "operator")
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' does not have permission to access this resource"
            )
        
        return current_user
    
    return role_checker


async def log_request(request: Request, call_next):
    """Middleware to log all requests.
    
    Args:
        request: FastAPI request object.
        call_next: Next middleware/endpoint.
        
    Returns:
        Response from next middleware/endpoint.
    """
    logger.info(f"{request.method} {request.url.path}")
    
    response = await call_next(request)
    
    logger.info(f"Response status: {response.status_code}")
    
    return response


async def cors_middleware(request: Request, call_next):
    """CORS middleware for cross-origin requests.
    
    Args:
        request: FastAPI request object.
        call_next: Next middleware/endpoint.
        
    Returns:
        Response with CORS headers.
    """
    response = await call_next(request)
    
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    return response


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per window.
            window_seconds: Time window in seconds.
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limit.
        
        Args:
            identifier: Unique identifier (e.g., user_id, IP).
            
        Returns:
            True if within limit, False otherwise.
        """
        now = datetime.utcnow().timestamp()
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        self.requests[identifier] = [
            ts for ts in self.requests[identifier]
            if now - ts < self.window_seconds
        ]
        
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        self.requests[identifier].append(now)
        return True


def rate_limit_dependency(limiter: RateLimiter):
    """Dependency for rate limiting.
    
    Args:
        limiter: RateLimiter instance.
        
    Returns:
        Dependency function.
    """
    def check_limit(current_user: dict = Depends(get_current_user)):
        identifier = current_user.get("user_id", "anonymous")
        
        if not limiter.check_rate_limit(identifier):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        return current_user
    
    return check_limit
