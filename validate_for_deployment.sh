#!/bin/bash
set -e

echo "🚀 MCP Host Pre-Deployment Validation"
echo "======================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
WARNINGS=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "${RED}❌ $2${NC}"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
    WARNINGS=$((WARNINGS + 1))
}

info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

echo "📋 Pre-deployment validation checks..."
echo ""

# 1. Directory Structure Validation
echo "📁 Checking project structure..."
[ -f "README.md" ] && test_result 0 "README.md exists" || test_result 1 "README.md missing"
[ -d "backend" ] && test_result 0 "Backend directory exists" || test_result 1 "Backend directory missing"
[ -d "frontend" ] && test_result 0 "Frontend directory exists" || test_result 1 "Frontend directory missing"
[ -f "docker-compose.yml" ] && test_result 0 "Docker Compose file exists" || test_result 1 "Docker Compose missing"
[ -f ".env.example" ] && test_result 0 "Environment template exists" || test_result 1 ".env.example missing"

# 2. Backend Validation
echo ""
echo "🐍 Validating backend..."
[ -f "backend/requirements.txt" ] && test_result 0 "Requirements file exists" || test_result 1 "Requirements missing"
[ -f "backend/Dockerfile" ] && test_result 0 "Backend Dockerfile exists" || test_result 1 "Backend Dockerfile missing"
[ -d "backend/src" ] && test_result 0 "Source directory exists" || test_result 1 "Source directory missing"

# Check core Python files
if [ -d "backend/src" ]; then
    cd backend
    python3 -m py_compile src/server.py 2>/dev/null && test_result 0 "server.py syntax valid" || test_result 1 "server.py syntax error"
    python3 -m py_compile src/gateway.py 2>/dev/null && test_result 0 "gateway.py syntax valid" || test_result 1 "gateway.py syntax error"
    python3 -m py_compile src/models.py 2>/dev/null && test_result 0 "models.py syntax valid" || test_result 1 "models.py syntax error"
    python3 -m py_compile src/config.py 2>/dev/null && test_result 0 "config.py syntax valid" || test_result 1 "config.py syntax error"
    python3 -m py_compile src/auth.py 2>/dev/null && test_result 0 "auth.py syntax valid" || test_result 1 "auth.py syntax error"
    python3 -m py_compile src/adapters/n8n.py 2>/dev/null && test_result 0 "n8n.py syntax valid" || test_result 1 "n8n.py syntax error"
    cd ..
fi

# 3. Frontend Validation
echo ""
echo "🌐 Validating frontend..."
[ -f "frontend/package.json" ] && test_result 0 "package.json exists" || test_result 1 "package.json missing"
[ -f "frontend/next.config.js" ] && test_result 0 "Next.js config exists" || test_result 1 "Next.js config missing"

if [ -f "frontend/package.json" ]; then
    # Check if package.json is valid JSON
    python3 -c "import json; json.load(open('frontend/package.json'))" 2>/dev/null && test_result 0 "package.json valid JSON" || test_result 1 "package.json invalid JSON"
fi

# 4. Docker Configuration Validation
echo ""
echo "🐳 Validating Docker configuration..."

# Check docker-compose.yml syntax
if command -v python3 >/dev/null 2>&1; then
    python3 -c "
import yaml
try:
    with open('docker-compose.yml', 'r') as f:
        yaml.safe_load(f)
    print('✅ docker-compose.yml valid YAML')
except Exception as e:
    print('❌ docker-compose.yml invalid:', e)
    exit(1)
" && test_result 0 "docker-compose.yml syntax valid" || test_result 1 "docker-compose.yml syntax error"
fi

# Check Dockerfile syntax
if [ -f "backend/Dockerfile" ]; then
    # Basic Dockerfile validation
    grep -q "FROM" backend/Dockerfile && test_result 0 "Dockerfile has FROM instruction" || test_result 1 "Dockerfile missing FROM"
    grep -q "COPY\|ADD" backend/Dockerfile && test_result 0 "Dockerfile copies files" || warning "Dockerfile doesn't copy files"
    grep -q "CMD\|ENTRYPOINT" backend/Dockerfile && test_result 0 "Dockerfile has startup command" || test_result 1 "Dockerfile missing startup command"
fi

# 5. Environment Configuration
echo ""
echo "⚙️ Validating environment configuration..."

if [ -f ".env.example" ]; then
    # Check for required environment variables
    grep -q "SECRET_KEY" .env.example && test_result 0 "SECRET_KEY defined" || test_result 1 "SECRET_KEY missing"
    grep -q "DATABASE_URL" .env.example && test_result 0 "DATABASE_URL defined" || warning "DATABASE_URL not defined"
    grep -q "OAUTH_CLIENT_ID" .env.example && test_result 0 "OAuth config defined" || warning "OAuth config not defined"

    # Check for production warnings
    if grep -q "dev-secret\|test-secret\|change-me" .env.example; then
        warning "Environment file contains development values - update for production"
    fi
fi

# 6. Security Validation
echo ""
echo "🛡️ Security validation..."

# Check for hardcoded secrets in code
if find backend/src -name "*.py" -exec grep -l "password\|secret\|key.*=" {} \; | grep -v __pycache__ >/dev/null 2>&1; then
    warning "Potential hardcoded secrets found in Python files"
else
    test_result 0 "No obvious hardcoded secrets in Python files"
fi

# Check for .env files in git (should be ignored)
if [ -f ".gitignore" ]; then
    grep -q "\.env$" .gitignore && test_result 0 ".env properly ignored in git" || warning ".env not in .gitignore"
else
    warning ".gitignore file missing"
fi

# 7. Dependency Validation
echo ""
echo "📦 Validating dependencies..."

# Check Python requirements
if [ -f "backend/requirements.txt" ]; then
    # Check for version pinning
    if grep -q ">=" backend/requirements.txt; then
        test_result 0 "Python dependencies have version constraints"
    else
        warning "Consider pinning Python dependency versions"
    fi

    # Check for known problematic dependencies
    if grep -q "sqlite3" backend/requirements.txt; then
        warning "sqlite3 listed as dependency (it's built-in)"
    fi
fi

# Check Node.js dependencies
if [ -f "frontend/package.json" ]; then
    if python3 -c "
import json
with open('frontend/package.json') as f:
    pkg = json.load(f)
    deps = pkg.get('dependencies', {})
    if 'next' in deps and 'react' in deps:
        print('✅ Core frontend dependencies present')
    else:
        print('❌ Missing core frontend dependencies')
        exit(1)
" 2>/dev/null; then
        test_result 0 "Core frontend dependencies present"
    else
        test_result 1 "Missing core frontend dependencies"
    fi
fi

# 8. API Endpoint Validation
echo ""
echo "🌐 Validating API structure..."

# Check for required endpoints in server.py
if [ -f "backend/src/server.py" ]; then
    grep -q "/health" backend/src/server.py && test_result 0 "Health endpoint defined" || test_result 1 "Health endpoint missing"
    grep -q "/mcp" backend/src/server.py && test_result 0 "MCP endpoint defined" || test_result 1 "MCP endpoint missing"
    grep -q "oauth" backend/src/server.py && test_result 0 "OAuth endpoints defined" || warning "OAuth endpoints not found"
fi

# 9. Documentation Validation
echo ""
echo "📚 Validating documentation..."
[ -f "CLAUDE.md" ] && test_result 0 "CLAUDE.md documentation exists" || warning "CLAUDE.md missing"
[ -f "README.md" ] && test_result 0 "README.md exists" || test_result 1 "README.md missing"

# Check if README has basic content
if [ -f "README.md" ]; then
    grep -q "MCP Host\|install\|usage" README.md && test_result 0 "README has basic content" || warning "README needs more content"
fi

# 10. Port and Service Configuration
echo ""
echo "🔌 Validating port configuration..."

# Check for port conflicts in docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    if grep -q "3000.*3000\|8000.*8000" docker-compose.yml; then
        test_result 0 "Standard ports configured (3000, 8000)"
    else
        warning "Non-standard ports configured - ensure they're available"
    fi
fi

# Final Summary
echo ""
echo "📊 Validation Summary"
echo "===================="
echo -e "${GREEN}✅ Checks Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}❌ Checks Failed: $CHECKS_FAILED${NC}"
echo -e "${YELLOW}⚠️ Warnings: $WARNINGS${NC}"

echo ""
if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 Ready for deployment!${NC}"
    echo ""
    echo "🚀 Next steps for GitHub + Coolify deployment:"
    echo "1. Create GitHub repository"
    echo "2. Push code: git init && git add . && git commit -m 'Initial MCP Host implementation'"
    echo "3. git remote add origin <your-repo-url> && git push -u origin main"
    echo "4. In Coolify:"
    echo "   - Create new resource → Application"
    echo "   - Connect to your GitHub repo"
    echo "   - Set environment variables:"
    echo "     * SECRET_KEY (generate a secure 32+ character string)"
    echo "     * OAUTH_CLIENT_ID (from ChatGPT if using OAuth)"
    echo "     * OAUTH_CLIENT_SECRET (from ChatGPT if using OAuth)"
    echo "   - Deploy!"
    echo ""
    echo "🔑 Important: Generate a secure SECRET_KEY for production!"
    echo "Example: openssl rand -base64 32"
else
    echo -e "${RED}⚠️ Fix the failed checks before deployment${NC}"
    echo ""
    echo "🔧 Common fixes:"
    echo "- Ensure all Python files have correct syntax"
    echo "- Add missing configuration files"
    echo "- Fix Docker configuration issues"
    echo "- Add proper environment variable templates"
fi

if [ $WARNINGS -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}💡 Address warnings for better security and reliability${NC}"
fi