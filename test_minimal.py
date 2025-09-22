#!/usr/bin/env python3
"""
Minimal test for MCP Host backend functionality
Tests core imports and basic functionality without full server startup
"""
import sys
import os

# Ensure we're using the backend src directory, not SuperClaude config
backend_src = os.path.join(os.path.dirname(__file__), 'backend', 'src')
sys.path.insert(0, backend_src)

def test_imports():
    """Test that all core modules can be imported"""
    try:
        from config import settings
        print("✅ Config import successful")

        from models import MCPServer, TransportType, ServerStatus
        print("✅ Models import successful")

        from auth import create_access_token, verify_token
        print("✅ Auth import successful")

        # Test gateway import (this was where we had the missing import issue)
        from gateway import MCPServerManager, MCPGateway
        print("✅ Gateway import successful")

        # Test n8n adapter import
        from adapters.n8n import N8NAdapter
        print("✅ N8N adapter import successful")

        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without database"""
    try:
        from models import TransportType, ServerStatus

        # Test enum values
        assert TransportType.STDIO == "stdio"
        assert TransportType.HTTP == "http"
        assert ServerStatus.ACTIVE == "active"
        print("✅ Enum values correct")

        from auth import create_access_token
        # Test token creation (mock)
        token = create_access_token({"sub": "test"})
        assert isinstance(token, str)
        print("✅ Token creation functional")

        return True
    except Exception as e:
        print(f"❌ Basic functionality error: {e}")
        return False

def test_n8n_adapter():
    """Test N8N adapter functionality"""
    try:
        from adapters.n8n import N8NAdapter

        adapter = N8NAdapter()

        # Test config creation
        config = adapter.create_n8n_server_config(
            name="test-n8n",
            n8n_api_url="http://localhost:5678",
            n8n_api_key="test-key"
        )

        assert config["name"] == "test-n8n"
        assert config["command"] == "npx"
        assert "@n8n-mcp/server" in config["args"]
        assert config["env"]["N8N_API_URL"] == "http://localhost:5678"
        print("✅ N8N adapter config creation successful")

        return True
    except Exception as e:
        print(f"❌ N8N adapter error: {e}")
        return False

def main():
    print("🧪 MCP Host Minimal Backend Test")
    print("=================================")

    results = []

    print("\n📦 Testing imports...")
    results.append(test_imports())

    print("\n⚙️ Testing basic functionality...")
    results.append(test_basic_functionality())

    print("\n🔧 Testing N8N adapter...")
    results.append(test_n8n_adapter())

    print(f"\n📊 Results: {sum(results)}/{len(results)} tests passed")

    if all(results):
        print("🎉 All minimal tests passed! Core functionality looks good.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())