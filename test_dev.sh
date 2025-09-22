#!/bin/bash
set -e

echo "🚀 MCP Host Development Testing"
echo "==============================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}This script tests MCP Host in development mode without Docker${NC}"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is required${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js found${NC}"

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Please run this script from the MCP Host root directory${NC}"
    exit 1
fi
echo -e "${GREEN}✅ In correct directory${NC}"

# Set up environment
echo ""
echo "⚙️  Setting up environment..."

if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env file${NC}"
    cp .env.example .env
    # Add development-specific settings
    cat >> .env << EOF

# Development settings
ENVIRONMENT=development
DEBUG=true
HOST=127.0.0.1
PORT=8000
SECRET_KEY=dev-secret-key-for-local-testing-32-chars-minimum
DATABASE_URL=sqlite:///./dev_mcp_host.db
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Frontend settings
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
EOF
    echo -e "${GREEN}✅ .env file created${NC}"
else
    echo -e "${GREEN}✅ .env file exists${NC}"
fi

# Backend setup
echo ""
echo "🐍 Setting up backend..."

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating Python virtual environment${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Install dependencies
echo -e "${YELLOW}📦 Installing Python dependencies${NC}"
pip install -q -r requirements.txt

# Test import
echo -e "${YELLOW}🧪 Testing Python imports${NC}"
python3 -c "
try:
    from src.config import settings
    from src.models import MCPServer
    from src.auth import create_access_token
    print('✅ All imports successful')
except Exception as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

cd ..

# Frontend setup
echo ""
echo "🌐 Setting up frontend..."

cd frontend

# Install dependencies
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing Node.js dependencies${NC}"
    npm install
else
    echo -e "${GREEN}✅ Node modules exist${NC}"
fi

# Test TypeScript compilation
echo -e "${YELLOW}🧪 Testing TypeScript compilation${NC}"
npm run type-check

cd ..

echo ""
echo -e "${GREEN}🎉 Development environment setup complete!${NC}"
echo ""
echo "🚀 To start development:"
echo ""
echo -e "${BLUE}Backend (Terminal 1):${NC}"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python -m uvicorn src.server:app --reload --host 127.0.0.1 --port 8000"
echo ""
echo -e "${BLUE}Frontend (Terminal 2):${NC}"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "📍 Development URLs:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Health Check: http://localhost:8000/health"
echo ""
echo "🧪 To run full Docker tests:"
echo "  ./test_local.sh"