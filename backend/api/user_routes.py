"""
User Management and Authentication API Routes

Provides endpoints for:
- User registration and login
- User listing by role (for second opinion requests)
- Authentication via JWT tokens
"""

from datetime import datetime, timedelta
from typing import List, Optional
import secrets
import hashlib
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from db import get_db, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["Users"])

# Simple session store (in production, use Redis or JWT)
active_sessions = {}


# === Schemas ===

class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    password: str
    full_name: str
    role: str  # 'manager', 'project_chief', 'technician'


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserListItem(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    success: bool
    user: Optional[UserResponse]
    session_token: Optional[str]
    message: str


# === Helper Functions ===

def hash_password(password: str) -> str:
    """Simple password hashing using SHA256 (use bcrypt in production)."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == password_hash


def get_current_user_from_session(session_token: str, db: Session) -> Optional[User]:
    """Get user from session token."""
    if session_token in active_sessions:
        user_id = active_sessions[session_token]["user_id"]
        return db.query(User).filter(User.id == user_id, User.is_active == True).first()
    return None


# === Endpoints ===

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user.
    
    Roles: manager, project_chief, technician
    """
    # Validate role
    valid_roles = ['manager', 'project_chief', 'technician']
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
    
    # Check if username exists
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email exists
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=True,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"✅ New user registered: {user.username} ({user.role})")
    return user


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Login with username and password.
    
    Returns a session token for subsequent requests.
    """
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is disabled")
    
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Generate session token
    session_token = secrets.token_urlsafe(32)
    active_sessions[session_token] = {
        "user_id": user.id,
        "username": user.username,
        "created_at": datetime.utcnow(),
    }
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    logger.info(f"✅ User logged in: {user.username}")
    
    return LoginResponse(
        success=True,
        user=user,
        session_token=session_token,
        message="Login successful"
    )


@router.post("/logout")
async def logout(session_token: str):
    """Logout and invalidate session."""
    if session_token in active_sessions:
        del active_sessions[session_token]
        return {"success": True, "message": "Logged out successfully"}
    return {"success": False, "message": "Session not found"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    session_token: str,
    db: Session = Depends(get_db),
):
    """Get current logged-in user's info."""
    user = get_current_user_from_session(session_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.get("/", response_model=List[UserListItem])
async def list_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db),
):
    """
    List all users, optionally filtered by role.
    
    Used for:
    - Displaying user list for managers
    - Selecting reviewers for second opinions
    """
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    users = query.order_by(User.full_name).all()
    return users


@router.get("/technicians", response_model=List[UserListItem])
async def list_technicians(
    exclude_user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    List all active technicians (for second opinion requests).
    
    Excludes the requesting user if exclude_user_id is provided.
    """
    query = db.query(User).filter(
        User.role == "technician",
        User.is_active == True
    )
    
    if exclude_user_id:
        query = query.filter(User.id != exclude_user_id)
    
    return query.order_by(User.full_name).all()


@router.get("/project-chiefs", response_model=List[UserListItem])
async def list_project_chiefs(
    db: Session = Depends(get_db),
):
    """
    List all active project chiefs (for escalating to senior reviewers).
    """
    users = db.query(User).filter(
        User.role == "project_chief",
        User.is_active == True
    ).order_by(User.full_name).all()
    
    return users


@router.get("/reviewers", response_model=List[UserListItem])
async def list_available_reviewers(
    exclude_user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    List all users who can receive second opinion requests.
    
    Returns both technicians and project chiefs (excluding current user).
    This is the main endpoint for the "Request Second Opinion" feature.
    """
    query = db.query(User).filter(
        User.role.in_(["technician", "project_chief"]),
        User.is_active == True
    )
    
    if exclude_user_id:
        query = query.filter(User.id != exclude_user_id)
    
    return query.order_by(User.role.desc(), User.full_name).all()  # project_chief first


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    """Deactivate a user account (manager only in production)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = False
    db.commit()
    
    logger.info(f"User deactivated: {user.username}")
    return {"success": True, "message": f"User {user.username} deactivated"}


@router.patch("/{user_id}/activate")
async def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    """Activate a user account (manager only in production)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = True
    db.commit()
    
    logger.info(f"User activated: {user.username}")
    return {"success": True, "message": f"User {user.username} activated"}
