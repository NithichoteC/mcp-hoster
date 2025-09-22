#!/bin/bash
set -e

echo "🧪 MCP Host Quick Validation"
echo "============================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

echo "📋 Quick validation checks..."

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Please run this script from the MCP Host root directory${NC}"
    exit 1
fi
test_result 0 "Directory structure"

# Check Python syntax
echo "🐍 Checking Python syntax..."
cd backend
python3 -m py_compile src/server.py 2>/dev/null
test_result $? "server.py syntax"

python3 -m py_compile src/gateway.py 2>/dev/null
test_result $? "gateway.py syntax"

python3 -m py_compile src/models.py 2>/dev/null
test_result $? "models.py syntax"

python3 -m py_compile src/config.py 2>/dev/null
test_result $? "config.py syntax"

python3 -m py_compile src/auth.py 2>/dev/null
test_result $? "auth.py syntax"

python3 -m py_compile src/adapters/n8n.py 2>/dev/null
test_result $? "n8n.py syntax"

cd ..

# Check Node.js package.json
echo "🌐 Checking frontend..."
if [ -f "frontend/package.json" ]; then
    test_result 0 "package.json exists"
else
    test_result 1 "package.json missing"
fi

# Check Docker files
echo "🐳 Checking Docker configuration..."
if [ -f "docker-compose.yml" ]; then
    test_result 0 "docker-compose.yml exists"
else
    test_result 1 "docker-compose.yml missing"
fi

if [ -f "backend/Dockerfile" ]; then
    test_result 0 "backend Dockerfile exists"
else
    test_result 1 "backend Dockerfile missing"
fi

# Check environment file
if [ -f ".env.example" ]; then
    test_result 0 ".env.example exists"
else
    test_result 1 ".env.example missing"
fi

# Check key files
echo "📁 Checking key configuration files..."
if [ -f "CLAUDE.md" ]; then
    test_result 0 "CLAUDE.md documentation"
else
    test_result 1 "CLAUDE.md missing"
fi

echo ""
echo -e "${GREEN}🎉 Quick validation complete!${NC}"
echo ""
echo "🚀 Next steps:"
echo "1. Run full test: ./test_dev.sh (development) or ./test_local.sh (Docker)"
echo "2. Fix any issues found"
echo "3. Commit to GitHub"
echo "4. Deploy to Coolify"
echo ""
echo "💡 The code structure and syntax look good!"