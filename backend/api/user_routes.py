"""
User Management and Authentication API Routes

Provides endpoints for:
- User registration and login
- User listing by role (RadikalUser, Chief, Manager)
- Role-based access control
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

from db import get_db, User, UserRole

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
    role: str  # 'radikal_user', 'chief', 'manager'
    supervisor_id: Optional[int] = None  # Required for radikal_user


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
    supervisor_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class UserListItem(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    supervisor_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    success: bool
    user: Optional[UserResponse]
    session_token: Optional[str]
    message: str
    permissions: Optional[dict] = None  # Role-based permissions


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
    
    Roles:
    - radikal_user: Can use models, perform analyses, view other RadikalUsers' results
    - chief: Supervises RadikalUsers, reviews analyses, requests changes, adds comments
    - manager: Views history, analysis results, activity diagrams, sees change requests
    """
    # Validate role
    valid_roles = UserRole.all_roles()
    if user_data.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
    
    # RadikalUsers must have a supervisor (Chief)
    if user_data.role == UserRole.RADIKAL_USER and user_data.supervisor_id:
        supervisor = db.query(User).filter(
            User.id == user_data.supervisor_id,
            User.role == UserRole.CHIEF,
            User.is_active == True
        ).first()
        if not supervisor:
            raise HTTPException(
                status_code=400,
                detail="Invalid supervisor_id. Must be an active Chief."
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
        supervisor_id=user_data.supervisor_id,
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
        "role": user.role,
        "created_at": datetime.utcnow(),
    }
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    logger.info(f"✅ User logged in: {user.username} (role: {user.role})")
    
    # Build permissions based on role
    permissions = {
        "can_use_models": UserRole.can_use_models(user.role),
        "can_review": UserRole.can_review(user.role),
        "can_request_changes": UserRole.can_request_changes(user.role),
        "can_add_comments": UserRole.can_add_comments(user.role),
        "can_view_all_users": UserRole.can_view_all_users(user.role),
        "can_view_change_requests": UserRole.can_view_change_requests(user.role),
    }
    
    return LoginResponse(
        success=True,
        user=user,
        session_token=session_token,
        message="Login successful",
        permissions=permissions
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


@router.get("/by-email/{email}")
async def get_user_by_email(
    email: str,
    db: Session = Depends(get_db),
):
    """
    Get user by email address.
    
    Used by the frontend to get role information for Supabase-authenticated users.
    """
    user = db.query(User).filter(User.email == email, User.is_active == True).first()
    if not user:
        # Return a default response for users not in the local database
        return {
            "id": None,
            "username": None,
            "email": email,
            "full_name": None,
            "role": "radikal_user",  # Default role
            "is_active": True,
            "supervisor_id": None,
            "supervisor_name": None,
        }
    
    # Get supervisor name if exists
    supervisor_name = None
    if user.supervisor_id:
        supervisor = db.query(User).filter(User.id == user.supervisor_id).first()
        if supervisor:
            supervisor_name = supervisor.full_name
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "supervisor_id": user.supervisor_id,
        "supervisor_name": supervisor_name,
    }


@router.get("/", response_model=List[UserListItem])
async def list_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = True,
    db: Session = Depends(get_db),
):
    """
    List all users, optionally filtered by role.
    
    Used for:
    - Displaying user list for managers and chiefs
    - Selecting reviewers
    """
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    users = query.order_by(User.full_name).all()
    return users


@router.get("/radikal-users", response_model=List[UserListItem])
async def list_radikal_users(
    exclude_user_id: Optional[int] = None,
    supervisor_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    List all active RadikalUsers.
    
    Args:
        exclude_user_id: Exclude this user from the list
        supervisor_id: Filter by supervisor (Chief) ID
    """
    query = db.query(User).filter(
        User.role == UserRole.RADIKAL_USER,
        User.is_active == True
    )
    
    if exclude_user_id:
        query = query.filter(User.id != exclude_user_id)
    
    if supervisor_id:
        query = query.filter(User.supervisor_id == supervisor_id)
    
    return query.order_by(User.full_name).all()


@router.get("/chiefs", response_model=List[UserListItem])
async def list_chiefs(
    db: Session = Depends(get_db),
):
    """
    List all active Chiefs.
    """
    users = db.query(User).filter(
        User.role == UserRole.CHIEF,
        User.is_active == True
    ).order_by(User.full_name).all()
    
    return users


@router.get("/managers", response_model=List[UserListItem])
async def list_managers(
    db: Session = Depends(get_db),
):
    """
    List all active Managers.
    """
    users = db.query(User).filter(
        User.role == UserRole.MANAGER,
        User.is_active == True
    ).order_by(User.full_name).all()
    
    return users


@router.get("/supervised-by/{chief_id}", response_model=List[UserListItem])
async def list_supervised_users(
    chief_id: int,
    db: Session = Depends(get_db),
):
    """
    List all RadikalUsers supervised by a specific Chief.
    """
    # Verify the chief exists
    chief = db.query(User).filter(
        User.id == chief_id,
        User.role == UserRole.CHIEF
    ).first()
    
    if not chief:
        raise HTTPException(status_code=404, detail="Chief not found")
    
    users = db.query(User).filter(
        User.supervisor_id == chief_id,
        User.is_active == True
    ).order_by(User.full_name).all()
    
    return users


# Legacy endpoints for backward compatibility
@router.get("/technicians", response_model=List[UserListItem])
async def list_technicians_legacy(
    exclude_user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    [DEPRECATED] Use /radikal-users instead.
    List all active RadikalUsers (for backward compatibility).
    """
    return await list_radikal_users(exclude_user_id=exclude_user_id, db=db)


@router.get("/project-chiefs", response_model=List[UserListItem])
async def list_project_chiefs_legacy(
    db: Session = Depends(get_db),
):
    """
    [DEPRECATED] Use /chiefs instead.
    List all active Chiefs (for backward compatibility).
    """
    return await list_chiefs(db=db)


@router.get("/reviewers", response_model=List[UserListItem])
async def list_available_reviewers(
    exclude_user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    List all users who can review analyses (Chiefs only).
    """
    query = db.query(User).filter(
        User.role == UserRole.CHIEF,
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
