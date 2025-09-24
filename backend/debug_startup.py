#!/usr/bin/env python3
"""
Debug startup script to test imports and environment
Run this before starting uvicorn to identify issues
"""
import os
import sys
import traceback
from pathlib import Path

def debug_startup():
    """Debug the startup environment"""
    print("🔍 MCP Host Startup Debug")
    print("=" * 50)

    # Environment info
    print(f"📍 Working directory: {os.getcwd()}")
    print(f"📍 Python executable: {sys.executable}")
    print(f"📍 Python version: {sys.version}")
    print(f"📍 Python path: {sys.path}")
    print(f"📍 PYTHONPATH env: {os.environ.get('PYTHONPATH', 'Not set')}")
    print()

    # Check if src directory exists
    src_path = Path("src")
    print(f"📁 Source directory exists: {src_path.exists()}")
    if src_path.exists():
        print(f"📁 Source directory contents: {list(src_path.iterdir())}")
    print()

    # Test basic imports
    print("🧪 Testing imports...")
    try:
        print("  ✓ Testing fastapi...")
        import fastapi
        print(f"    FastAPI version: {fastapi.__version__}")

        print("  ✓ Testing uvicorn...")
        import uvicorn
        print(f"    Uvicorn version: {uvicorn.__version__}")

        print("  ✓ Testing sqlalchemy...")
        import sqlalchemy
        print(f"    SQLAlchemy version: {sqlalchemy.__version__}")

        print("  ✓ Testing src.config...")
        from src.config import settings
        print(f"    Settings loaded: {settings.app_name}")

        print("  ✓ Testing src.database...")
        from src.database import init_db, get_db
        print("    Database modules imported")

        print("  ✓ Testing src.models...")
        from src.models import MCPServer
        print("    Models imported")

        print("  ✓ Testing src.server...")
        from src.server import app
        print("    FastAPI app imported")

        print("✅ All imports successful!")

    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False

    print()
    print("🚀 Startup debug completed successfully!")
    return True

if __name__ == "__main__":
    success = debug_startup()
    sys.exit(0 if success else 1)