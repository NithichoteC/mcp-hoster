# 🚀 MCP Host Deployment Guide

Complete guide for deploying MCP Host to GitHub and Coolify.

## ✅ Pre-Deployment Checklist

Run `./validate_for_deployment.sh` to verify everything is ready. You should see:
- ✅ 34+ checks passed
- ❌ 0 checks failed
- ⚠️ 2 or fewer warnings

## 📋 Step-by-Step Deployment

### 1. Initialize Git Repository

```bash
# In your MCP Host directory
git init
git add .
git commit -m "Initial MCP Host implementation

- FastAPI backend with MCP protocol support
- React/Next.js frontend dashboard
- Multi-transport support (STDIO, HTTP, SSE)
- OAuth2 authentication for ChatGPT integration
- Docker deployment configuration
- n8n-mcp adapter included"
```

### 2. Create GitHub Repository

1. Go to GitHub and create a new repository
2. Name it something like `mcp-host` or `my-mcp-host`
3. Set it to **Public** or **Private** (your choice)
4. Don't initialize with README (we already have one)

### 3. Push to GitHub

```bash
# Replace with your actual repository URL
git remote add origin https://github.com/yourusername/mcp-host.git
git branch -M main
git push -u origin main
```

### 4. Deploy to Coolify

#### A. Create New Application
1. Open Coolify dashboard
2. Click **"+ New"** → **"Resource"** → **"Application"**
3. Select **"Public Repository"**
4. Enter your GitHub repository URL: `https://github.com/yourusername/mcp-host`
5. Set branch to `main`

#### B. Configure Build Settings
1. **Build Pack**: Docker Compose
2. **Docker Compose File**: `docker-compose.yml` (default)
3. **Port**: `3000` (frontend will be exposed)

#### C. Set Environment Variables
Click **"Environment Variables"** and add:

**Required:**
```
SECRET_KEY=<generate-secure-32-char-string>
NODE_ENV=production
ENVIRONMENT=production
```

**For ChatGPT Integration (optional):**
```
OAUTH_CLIENT_ID=<from-chatgpt-custom-connector>
OAUTH_CLIENT_SECRET=<from-chatgpt-custom-connector>
```

**Database (optional - defaults to SQLite):**
```
DATABASE_URL=sqlite:///./mcp_host.db
```

**Additional (optional):**
```
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com
```

#### D. Generate Secure SECRET_KEY
```bash
# Generate a secure secret key
openssl rand -base64 32
# Example output: yRXnz9HGEjmZlJQGJ8K1vF2sB7N3P4T6uM8Y2wX5qA=
```

### 5. Deploy and Verify

1. Click **"Deploy"** in Coolify
2. Monitor the build logs
3. Once deployed, test the endpoints:

```bash
# Replace yourdomain.com with your actual domain
curl https://yourdomain.com/health
curl https://yourdomain.com/api/v1/servers
```

## 🔧 Post-Deployment Configuration

### Create Your First API Key
1. Visit `https://yourdomain.com`
2. Navigate to the API Keys section
3. Create a new key with permissions: `["mcp:read", "mcp:write"]`
4. Save the generated key securely

### Add Your First MCP Server

#### Example: n8n-mcp Server
```bash
curl -X POST https://yourdomain.com/api/v1/servers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "name": "n8n-mcp",
    "description": "n8n workflow automation MCP server",
    "command": "npx",
    "args": ["@n8n-mcp/server"],
    "transport_type": "stdio",
    "auto_restart": true
  }'
```

#### Example: GitHub MCP Server
```bash
curl -X POST https://yourdomain.com/api/v1/servers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "name": "github-mcp",
    "description": "GitHub integration MCP server",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": "your_github_token"
    },
    "transport_type": "stdio",
    "auto_restart": true
  }'
```

## 🤖 Connect to ChatGPT

### 1. Configure Custom Connector
1. In ChatGPT, go to Settings → Beta Features
2. Enable "Custom GPTs" and "Actions"
3. Create a new Custom GPT
4. In Actions, add:

**Authentication Type**: OAuth 2.0
**Client ID**: `<your-oauth-client-id>`
**Client Secret**: `<your-oauth-client-secret>`
**Authorization URL**: `https://yourdomain.com/auth/authorize`
**Token URL**: `https://yourdomain.com/auth/token`
**Scope**: `mcp:read mcp:write`

### 2. Import OpenAPI Schema
```bash
# Get the OpenAPI schema for ChatGPT
curl https://yourdomain.com/.well-known/openapi.json
```
Copy the response and paste it into ChatGPT's Actions schema.

## 🔍 Monitoring and Maintenance

### Health Checks
```bash
# System health
curl https://yourdomain.com/health

# Server status
curl https://yourdomain.com/api/v1/servers \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Logs
In Coolify, go to your application → **Logs** to monitor:
- Application startup
- MCP server connections
- API requests
- Error messages

### Updates
To update your deployment:
1. Make changes locally
2. Commit and push to GitHub: `git push`
3. Coolify will auto-deploy if you enabled continuous deployment
4. Or manually trigger deployment in Coolify dashboard

## 🆘 Troubleshooting

### Common Issues

**Build Fails**
- Check Docker compose syntax: `./validate_for_deployment.sh`
- Verify all files are committed to git
- Check Coolify build logs for specific errors

**App Won't Start**
- Verify SECRET_KEY is set and at least 32 characters
- Check environment variables are correctly set
- Look for error messages in Coolify logs

**MCP Server Won't Connect**
- Ensure the MCP server package is available via npm
- Check server logs for connection errors
- Verify transport_type matches server capabilities

**OAuth Issues**
- Verify OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET are correct
- Check redirect URLs match exactly
- Ensure OAuth endpoints are accessible

### Support Resources
- Coolify Documentation: https://coolify.io/docs
- MCP Protocol Spec: https://spec.modelcontextprotocol.io
- FastMCP Documentation: https://github.com/jlowin/fastmcp

## 🎉 Success!

Your MCP Host is now running and ready to connect any GitHub-available MCP server to AI agents like ChatGPT, Claude, or others!

**What you can do now:**
- Add more MCP servers through the web interface
- Connect multiple AI agents to the same MCP servers
- Monitor usage and performance through the dashboard
- Scale by adding more server instances