#!/usr/bin/env python3
"""
Sync existing backend users to Supabase auth.users and accounts tables.
This script creates Supabase auth accounts for users that exist in the backend users table.
"""

import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
from supabase import create_client, Client
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine
from db.models import User
import bcrypt

# Load environment variables
load_dotenv()

def get_supabase_client() -> Client:
    """Get Supabase client."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Service role key for admin operations
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env file.\n"
            "You can find these in frontend-makerkit/apps/web/.env.local"
        )
    
    return create_client(supabase_url, supabase_key)

def create_supabase_user(supabase: Client, user: User, default_password: str = "RadiKal2024!"):
    """Create a user in Supabase auth and accounts table."""
    try:
        # Check if user already exists in Supabase
        try:
            # Try to get user by email
            response = supabase.auth.admin.list_users()
            existing_users = [u for u in response if u.email == user.email]
            
            if existing_users:
                print(f"  ℹ️  User {user.email} already exists in Supabase")
                return existing_users[0]
        except Exception as e:
            print(f"  ⚠️  Could not check existing users: {e}")
        
        # Create user in Supabase auth
        print(f"  📧 Creating Supabase auth user for: {user.email}")
        
        auth_response = supabase.auth.admin.create_user({
            "email": user.email,
            "password": default_password,
            "email_confirm": True,  # Auto-confirm email
            "user_metadata": {
                "name": user.full_name,
                "full_name": user.full_name,
                "role": user.role
            }
        })
        
        if auth_response.user:
            print(f"  ✅ Created auth user: {user.email}")
            print(f"     User ID: {auth_response.user.id}")
            print(f"     Default password: {default_password}")
            
            # The accounts table entry should be created automatically by the trigger
            # But let's verify it was created
            import time
            time.sleep(1)  # Wait for trigger to execute
            
            account = supabase.table("accounts").select("*").eq("email", user.email).execute()
            
            if account.data:
                print(f"  ✅ Account record created automatically")
            else:
                print(f"  ⚠️  Account record not found, creating manually...")
                supabase.table("accounts").insert({
                    "id": str(auth_response.user.id),
                    "email": user.email,
                    "name": user.full_name,
                }).execute()
            
            return auth_response.user
        else:
            print(f"  ❌ Failed to create auth user for {user.email}")
            return None
            
    except Exception as e:
        print(f"  ❌ Error creating Supabase user {user.email}: {e}")
        return None

def main():
    """Main sync routine."""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║    Sync Backend Users to Supabase Authentication        ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Get Supabase client
        print("🔗 Connecting to Supabase...")
        supabase = get_supabase_client()
        print("✅ Connected to Supabase")
        
        # Get database session
        print("\n🔗 Connecting to backend database...")
        db: Session = SessionLocal()
        print("✅ Connected to backend database")
        
        # Get all users from backend
        print("\n📋 Fetching users from backend database...")
        users = db.query(User).all()
        print(f"✅ Found {len(users)} users in backend database")
        
        if not users:
            print("\n⚠️  No users found in backend database.")
            print("   Run 'python add_sample_data.py' to create sample users first.")
            return
        
        # Default password for all created users
        default_password = "RadiKal2024!"
        
        print(f"\n🔄 Creating Supabase auth accounts...")
        print(f"   Default password for all users: {default_password}")
        print(f"   Users will be able to change this after first login.\n")
        
        created_count = 0
        existing_count = 0
        failed_count = 0
        
        for user in users:
            print(f"\n👤 Processing user: {user.username} ({user.email})")
            print(f"   Role: {user.role}")
            print(f"   Full Name: {user.full_name}")
            
            result = create_supabase_user(supabase, user, default_password)
            
            if result:
                if "already exists" in str(result):
                    existing_count += 1
                else:
                    created_count += 1
            else:
                failed_count += 1
        
        # Print summary
        print("\n" + "="*60)
        print("📊 SYNC SUMMARY")
        print("="*60)
        print(f"✅ Created: {created_count}")
        print(f"ℹ️  Already existed: {existing_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📋 Total processed: {len(users)}")
        
        if created_count > 0:
            print(f"\n🔑 Default password for new accounts: {default_password}")
            print("   Users should change this after first login.")
        
        print("\n✅ Sync complete!")
        print("\n📝 Next steps:")
        print("   1. Users can now log in at: http://localhost:3000/auth/sign-in")
        print(f"   2. Use their email and password: {default_password}")
        print("   3. They should update their password in profile settings")
        
        db.close()
        
    except Exception as e:
        print(f"\n❌ Error during sync: {e}")
        print(f"\nDetails: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
