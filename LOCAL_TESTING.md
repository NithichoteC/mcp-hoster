#!/bin/bash
set -e

echo "🧪 MCP Host Local Testing Script"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ $2${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

echo "📋 Pre-flight checks..."

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Creating .env file from template${NC}"
    cp .env.example .env
    echo "SECRET_KEY=test-secret-key-for-local-testing-32-chars" >> .env
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# Check if ports are available
if netstat -tuln | grep -q ":8000 "; then
    echo -e "${YELLOW}⚠️  Port 8000 is in use. Stopping existing services...${NC}"
    docker-compose down 2>/dev/null || true
    pkill -f "uvicorn" 2>/dev/null || true
fi

if netstat -tuln | grep -q ":3000 "; then
    echo -e "${YELLOW}⚠️  Port 3000 is in use. Stopping existing services...${NC}"
    pkill -f "next" 2>/dev/null || true
fi

echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

echo "🔍 Testing backend endpoints..."

# Test health endpoint
curl -s -f http://localhost:8000/health > /dev/null
test_result $? "Backend health check"

# Test API endpoints
curl -s -f http://localhost:8000/api/v1/servers > /dev/null
test_result $? "Servers API endpoint"

# Test OAuth2 metadata
curl -s -f http://localhost:8000/.well-known/oauth-authorization-server > /dev/null
test_result $? "OAuth2 metadata endpoint"

echo "🌐 Testing frontend..."

# Test frontend
curl -s -f http://localhost:3000 > /dev/null
test_result $? "Frontend accessibility"

echo "🔧 Testing MCP functionality..."

# Create test API key
API_KEY_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/keys \
  -H "Content-Type: application/json" \
  -d '{"name": "test-key", "permissions": ["mcp:read", "mcp:write", "admin"]}' 2>/dev/null)

if echo "$API_KEY_RESPONSE" | grep -q "api_key"; then
    API_KEY=$(echo "$API_KEY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['api_key'])" 2>/dev/null)
    test_result 0 "API key creation"
    echo -e "${GREEN}🔑 API Key: $API_KEY${NC}"
else
    test_result 1 "API key creation"
    API_KEY=""
fi

# Test MCP protocol endpoint
curl -s -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}}}' > /dev/null
test_result $? "MCP protocol endpoint"

echo "📦 Testing server management..."

# Add test server
SERVER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/servers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "name": "test-echo-server",
    "description": "Test echo server",
    "command": "echo",
    "args": ["Hello MCP"],
    "transport_type": "stdio"
  }' 2>/dev/null)

if echo "$SERVER_RESPONSE" | grep -q "test-echo-server"; then
    test_result 0 "Test server creation"
    SERVER_ID=$(echo "$SERVER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
    echo -e "${GREEN}📋 Server ID: $SERVER_ID${NC}"
else
    test_result 1 "Test server creation"
fi

echo "🧪 Testing n8n MCP server (if available)..."

# Check if n8n-mcp is available
if command -v npx >/dev/null 2>&1; then
    # Try to install n8n-mcp
    echo "📦 Installing n8n-mcp server..."
    npm list -g @n8n-mcp/server >/dev/null 2>&1 || npm install -g @n8n-mcp/server >/dev/null 2>&1

    if npm list -g @n8n-mcp/server >/dev/null 2>&1; then
        # Add n8n server
        N8N_SERVER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/servers \
          -H "Content-Type: application/json" \
          -H "Authorization: Bearer $API_KEY" \
          -d '{
            "name": "n8n-mcp-test",
            "description": "n8n MCP server test",
            "command": "npx",
            "args": ["@n8n-mcp/server"],
            "transport_type": "stdio"
          }' 2>/dev/null)

        if echo "$N8N_SERVER_RESPONSE" | grep -q "n8n-mcp-test"; then
            test_result 0 "n8n MCP server setup"
        else
            test_result 1 "n8n MCP server setup"
        fi
    else
        test_result 1 "n8n MCP server installation"
    fi
else
    echo -e "${YELLOW}⚠️  Node.js/npm not available, skipping n8n test${NC}"
fi

echo "📊 Testing system metrics..."

# Test system status
SYSTEM_STATUS=$(curl -s http://localhost:8000/health)
if echo "$SYSTEM_STATUS" | grep -q "uptime_seconds"; then
    test_result 0 "System metrics collection"
    UPTIME=$(echo "$SYSTEM_STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin)['uptime_seconds'])" 2>/dev/null)
    echo -e "${GREEN}⏱️  System uptime: ${UPTIME}s${NC}"
else
    test_result 1 "System metrics collection"
fi

echo "🧹 Cleanup test resources..."

# List servers for cleanup
SERVERS=$(curl -s http://localhost:8000/api/v1/servers -H "Authorization: Bearer $API_KEY" 2>/dev/null)
if echo "$SERVERS" | grep -q "\[\]"; then
    echo -e "${GREEN}✅ No servers to clean up${NC}"
else
    echo -e "${YELLOW}🧹 Test servers will remain for manual inspection${NC}"
fi

echo ""
echo "📋 Test Summary"
echo "==============="
echo -e "${GREEN}✅ Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Tests Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Ready for deployment.${NC}"
    echo ""
    echo "🚀 Next steps:"
    echo "1. Commit code to GitHub"
    echo "2. Deploy to Coolify"
    echo "3. Configure production environment variables"
    echo ""
    echo "🌐 Access points:"
    echo "- Frontend: http://localhost:3000"
    echo "- Backend API: http://localhost:8000"
    echo "- Health Check: http://localhost:8000/health"
    echo "- API Docs: http://localhost:8000/docs"
    if [ ! -z "$API_KEY" ]; then
        echo "- API Key: $API_KEY"
    fi
else
    echo -e "${RED}⚠️  Some tests failed. Please check the logs above.${NC}"
    echo ""
    echo "🔍 Troubleshooting:"
    echo "- Check Docker logs: docker-compose logs"
    echo "- Verify .env configuration"
    echo "- Ensure ports 3000 and 8000 are available"
    exit 1
fi
EOF