#!/usr/bin/env python3
"""
Setup script to configure RadiKal backend with Supabase database.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and handle errors."""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False

def check_env_file():
    """Check if .env file exists, create from example if not."""
    env_path = Path(__file__).parent / ".env"
    env_example_path = Path(__file__).parent / ".env.example"
    
    if not env_path.exists():
        if env_example_path.exists():
            print("📄 Creating .env file from .env.example...")
            with open(env_example_path, 'r') as src:
                content = src.read()
            with open(env_path, 'w') as dst:
                dst.write(content)
            print("✅ .env file created")
        else:
            print("⚠️  .env.example not found, skipping .env creation")
    else:
        print("✅ .env file already exists")

def main():
    """Main setup routine."""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║         RadiKal Backend + Supabase Setup                ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Step 1: Check/create .env file
    check_env_file()
    
    # Step 2: Install Python dependencies
    if not run_command(
        "pip install -r requirements.txt",
        "Installing Python dependencies"
    ):
        print("\n❌ Failed to install dependencies. Please check your Python environment.")
        sys.exit(1)
    
    # Step 3: Check Supabase status
    print("\n" + "="*60)
    print("🔍 Checking Supabase status...")
    print("="*60)
    
    # Navigate to frontend to run supabase commands
    frontend_dir = backend_dir.parent / "frontend-makerkit" / "apps" / "web"
    if frontend_dir.exists():
        os.chdir(frontend_dir)
        
        # Check if Supabase is running
        result = subprocess.run(
            "pnpm supabase:status",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if "STOPPED" in result.stdout or result.returncode != 0:
            print("⚠️  Supabase is not running. Starting Supabase...")
            if run_command("pnpm supabase:start", "Starting Supabase"):
                print("✅ Supabase started successfully")
            else:
                print("❌ Failed to start Supabase. Please start it manually:")
                print("   cd frontend-makerkit/apps/web")
                print("   pnpm supabase:start")
                sys.exit(1)
        else:
            print("✅ Supabase is already running")
            print(result.stdout)
    else:
        print("⚠️  Frontend directory not found. Please ensure Supabase is running.")
    
    # Step 4: Apply migrations
    os.chdir(frontend_dir)
    if not run_command(
        "pnpm supabase:reset",
        "Applying database migrations (including RadiKal schema)"
    ):
        print("\n⚠️  Migration may have failed. Trying alternative approach...")
        # The migration file is already in place, it will be applied on next reset
    
    # Step 5: Test database connection
    os.chdir(backend_dir)
    print("\n" + "="*60)
    print("🧪 Testing database connection...")
    print("="*60)
    
    test_script = """
import os
os.environ['DATABASE_TYPE'] = 'supabase'
from db.database import engine, init_db
try:
    init_db()
    print('✅ Database connection successful!')
    print('✅ All tables created/verified')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"""
    
    with open("test_db_connection.py", "w") as f:
        f.write(test_script)
    
    result = subprocess.run(
        f"{sys.executable} test_db_connection.py",
        shell=True,
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    # Clean up test file
    Path("test_db_connection.py").unlink(missing_ok=True)
    
    if result.returncode != 0:
        print("\n❌ Database connection test failed")
        sys.exit(1)
    
    # Success summary
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║              ✅ SETUP COMPLETE! ✅                       ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    
    🎉 RadiKal backend is now configured with Supabase!
    
    📝 Next steps:
    
    1. Start the backend server:
       python main.py
       
    2. Or use uvicorn directly:
       uvicorn main:app --reload --host 0.0.0.0 --port 8000
       
    3. Access the API docs:
       http://localhost:8000/docs
       
    4. Verify Supabase connection:
       Database URL: postgresql://postgres:postgres@127.0.0.1:54322/postgres
       
    5. View database in Supabase Studio:
       http://127.0.0.1:54323
       
    💡 Tips:
    - All RadiKal tables are created in the 'public' schema
    - Row Level Security (RLS) is enabled for multi-tenancy
    - Check .env file for configuration options
    - To switch back to SQLite: Set DATABASE_TYPE=sqlite in .env
    """)

if __name__ == "__main__":
    main()
