"""
Script to add/update user role in RadiKal database.

Usage:
  python add_user_role.py <email> <role> [full_name]

Roles:
  - radikal_user: Standard user (can perform analysis)
  - chief: Project chief (can review analyses)
  - manager: Manager (full access)

Examples:
  python add_user_role.py john@example.com radikal_user "John Doe"
  python add_user_role.py boss@example.com manager "Big Boss"
"""

import sys
import hashlib
from db import get_db, User, UserRole

def add_or_update_user(email: str, role: str, full_name: str = None):
    """Add a new user or update existing user's role."""
    db = next(get_db())
    
    # Validate role
    valid_roles = ['radikal_user', 'chief', 'manager']
    if role not in valid_roles:
        print(f"Error: Invalid role '{role}'. Must be one of: {valid_roles}")
        return False
    
    # Check if user exists
    existing_user = db.query(User).filter(User.email == email).first()
    
    if existing_user:
        # Update existing user's role
        old_role = existing_user.role
        existing_user.role = role
        db.commit()
        print(f"Updated user '{email}' role from '{old_role}' to '{role}'")
        return True
    else:
        # Create new user
        username = email.split('@')[0]
        name = full_name or username.replace('.', ' ').title()
        
        new_user = User(
            username=username,
            email=email,
            password_hash=hashlib.sha256('temp123'.encode()).hexdigest(),
            full_name=name,
            role=role,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        print(f"Created new user '{email}' with role '{role}'")
        return True

def list_users():
    """List all users with their roles."""
    db = next(get_db())
    users = db.query(User).all()
    
    print("\n=== All Users ===")
    print(f"{'Email':<40} {'Role':<15} {'Full Name':<25}")
    print("-" * 80)
    for user in users:
        print(f"{user.email:<40} {user.role:<15} {user.full_name:<25}")
    print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        list_users()
        sys.exit(0)
    
    if sys.argv[1] == '--list':
        list_users()
        sys.exit(0)
    
    if len(sys.argv) < 3:
        print("Error: Please provide email and role")
        print(__doc__)
        sys.exit(1)
    
    email = sys.argv[1]
    role = sys.argv[2]
    full_name = sys.argv[3] if len(sys.argv) > 3 else None
    
    add_or_update_user(email, role, full_name)
    list_users()
