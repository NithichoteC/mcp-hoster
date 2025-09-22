@echo off
echo 🚀 MCP Host GitHub Push Script
echo ==============================

REM Remove .env file (contains secrets)
if exist .env del .env
echo ✅ Removed .env file for security

REM Initialize git if not already done
if not exist .git (
    git init
    git branch -M main
    echo ✅ Initialized git repository
)

REM Configure git (you may need to change these)
git config user.name "Your Name"
git config user.email "your.email@example.com"

REM Add all files
git add .
echo ✅ Added all files to git

REM Commit
git commit -m "Initial MCP Host implementation - Professional MCP server hosting solution"
echo ✅ Created commit

echo.
echo 🌐 Next steps:
echo 1. Go to GitHub.com and create a new repository named 'mcp-host'
echo 2. Copy the repository URL (like: https://github.com/yourusername/mcp-host.git)
echo 3. Run this command: git remote add origin YOUR_REPO_URL
echo 4. Run this command: git push -u origin main
echo.
echo Your repository will be ready for Coolify deployment!

pause