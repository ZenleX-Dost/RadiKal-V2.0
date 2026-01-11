"""
JWT Authentication and Authorization middleware.

Features:
- JWT token generation and validation
- Role-based access control (RBAC)
- Permission checks
- Token refresh mechanism
- Secure password hashing
"""

from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging
import os
import secrets

from db import get_db, User

logger = logging.getLogger(__name__)

# Secure configuration loading
def _get_secret_key() -> str:
    """Get JWT secret key securely."""
    # Try environment variable first
    secret = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET")
    
    if secret and secret not in [
        "dev-secret-key-change-in-production",
        "radikal-dev-secret-change-in-production",
        "your-secret-key-change-in-production",
        "changeme",
        "secret"
    ]:
        return secret
    
    # Try config module
    try:
        from core.config import settings
        if hasattr(settings, 'SECRET_KEY') and settings.SECRET_KEY:
            return settings.SECRET_KEY
    except ImportError:
        pass
    
    # In development, generate a random key (will change on restart)
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        raise RuntimeError(
            "SECURITY ERROR: JWT_SECRET_KEY must be set in production! "
            "Set the JWT_SECRET_KEY environment variable with a secure value. "
            "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
        )
    
    # Development fallback - generate random key with warning
    logger.warning(
        "[SECURITY] Using randomly generated JWT secret. "
        "Set JWT_SECRET_KEY environment variable for persistent sessions."
    )
    return secrets.token_urlsafe(64)

SECRET_KEY = _get_secret_key()
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """JWT token payload."""
    user_id: str
    email: str
    role: str
    account_id: Optional[str] = None
    exp: datetime


class UserContext(BaseModel):
    """Authenticated user context."""
    id: str
    email: str
    role: str
    account_id: Optional[str] = None
    permissions: List[str] = []


# Role hierarchy
ROLE_HIERARCHY = {
    "manager": 3,
    "project_chief": 2,
    "technician": 1,
    "guest": 0
}

# Permission mappings
ROLE_PERMISSIONS = {
    "manager": [
        "analysis:create",
        "analysis:read",
        "analysis:update",
        "analysis:delete",
        "review:create",
        "review:read",
        "review:assign",
        "review:approve",
        "custom_defects:create",
        "custom_defects:manage",
        "training:trigger",
        "users:manage",
        "analytics:view",
        "compliance:generate"
    ],
    "project_chief": [
        "analysis:create",
        "analysis:read",
        "analysis:update",
        "review:create",
        "review:read",
        "review:assign",
        "review:approve",
        "custom_defects:create",
        "analytics:view",
        "compliance:generate"
    ],
    "technician": [
        "analysis:create",
        "analysis:read",
        "review:create",
        "review:read",
        "analytics:view"
    ],
    "guest": [
        "analysis:read",
        "analytics:view"
    ]
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Token payload data
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData object
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        account_id: str = payload.get("account_id")
        exp: int = payload.get("exp")
        
        if user_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(
            user_id=user_id,
            email=email,
            role=role,
            account_id=account_id,
            exp=datetime.fromtimestamp(exp)
        )
    
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> UserContext:
    """
    Get current authenticated user from JWT token.
    
    Dependency for protected endpoints:
        @router.get("/protected")
        async def protected_route(user: UserContext = Depends(get_current_user)):
            return {"user_id": user.id}
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = decode_token(credentials.credentials)
    
    # Get user from database
    user = db.query(User).filter(User.id == token_data.user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    # Get permissions for role
    permissions = ROLE_PERMISSIONS.get(user.role, [])
    
    # Create user context
    user_context = UserContext(
        id=user.id,
        email=user.email,
        role=user.role,
        account_id=user.account_id,
        permissions=permissions
    )
    
    # Store in request state for access in other middleware
    request.state.user = user_context
    
    return user_context


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[UserContext]:
    """
    Get current user if authenticated, None otherwise.
    
    Use for endpoints that work with or without authentication:
        @router.get("/public")
        async def public_route(user: Optional[UserContext] = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user.email}"}
            return {"message": "Hello guest"}
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None


def require_role(required_role: str):
    """
    Require specific role or higher.
    
    Usage:
        @router.post("/admin")
        async def admin_route(user: UserContext = Depends(require_role("manager"))):
            return {"message": "Admin access granted"}
    """
    async def role_checker(user: UserContext = Depends(get_current_user)):
        user_level = ROLE_HIERARCHY.get(user.role, 0)
        required_level = ROLE_HIERARCHY.get(required_role, 999)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}"
            )
        
        return user
    
    return role_checker


def require_permission(permission: str):
    """
    Require specific permission.
    
    Usage:
        @router.post("/reviews/assign")
        async def assign_review(
            user: UserContext = Depends(require_permission("review:assign"))
        ):
            return {"message": "Review assigned"}
    """
    async def permission_checker(user: UserContext = Depends(get_current_user)):
        if permission not in user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}"
            )
        
        return user
    
    return permission_checker


def require_same_account(resource_account_id: str):
    """
    Require user belongs to same account (multi-tenancy).
    
    Usage:
        @router.get("/analysis/{analysis_id}")
        async def get_analysis(
            analysis_id: str,
            user: UserContext = Depends(get_current_user),
            db: Session = Depends(get_db)
        ):
            analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
            require_same_account(analysis.account_id)(user)
            return analysis
    """
    def account_checker(user: UserContext):
        if user.account_id != resource_account_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: resource belongs to different account"
            )
        return True
    
    return account_checker
