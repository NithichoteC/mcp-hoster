# MCP Host - Professional MCP Server Gateway

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Coolify](https://img.shields.io/badge/Coolify-Compatible-green.svg)](https://coolify.io/)

> **Connect any MCP server to any AI agent** - A professional, production-ready gateway for the Model Context Protocol

MCP Host is a comprehensive solution that allows you to connect any MCP (Model Context Protocol) server to any AI agent, including ChatGPT, Claude, and custom applications. Deploy with one click to Coolify and start connecting your tools and data sources to AI agents immediately.

## 🌟 Key Features

### 🔗 **Universal Connectivity**
- **ChatGPT Integration**: OAuth2-based custom connector support
- **Claude Desktop**: Native MCP protocol compatibility
- **API Access**: RESTful API for custom integrations
- **WebSocket Support**: Real-time communication

### 🚀 **Multi-Transport Support**
- **STDIO**: Traditional process-based communication
- **HTTP**: RESTful API integration
- **SSE**: Server-Sent Events for real-time updates
- **Streamable HTTP**: Modern MCP protocol (2025 spec)

### 🏗️ **Professional Infrastructure**
- **Docker-Native**: Container-first deployment
- **Auto-Scaling**: Kubernetes and Docker Swarm ready
- **Health Monitoring**: Comprehensive health checks
- **SSL/TLS**: Production-grade security

### 🎯 **GitHub Integration**
- **Auto-Discovery**: Automatically detect and configure MCP servers from GitHub
- **Popular Servers**: Curated list of community MCP servers
- **One-Click Setup**: Install servers directly from repositories

### 🔧 **Management Interface**
- **Web Dashboard**: React-based management interface
- **Real-Time Monitoring**: Live server status and metrics
- **Configuration Management**: Easy server setup and configuration
- **API Key Management**: Secure access control

## 📋 Table of Contents

1. [Quick Start](#-quick-start)
2. [Coolify Deployment](#-coolify-deployment)
3. [Manual Deployment](#-manual-deployment)
4. [Configuration](#-configuration)
5. [ChatGPT Integration](#-chatgpt-integration)
6. [Claude Integration](#-claude-integration)
7. [Adding MCP Servers](#-adding-mcp-servers)
8. [API Documentation](#-api-documentation)
9. [Troubleshooting](#-troubleshooting)
10. [Contributing](#-contributing)

## 🚀 Quick Start

### Option 1: Deploy to Coolify (Recommended)

1. **One-Click Deploy**:
   ```bash
   # Import this repository to Coolify
   https://github.com/your-org/mcp-host
   ```

2. **Configure Environment Variables**:
   - `SECRET_KEY`: Generate a random string (required)
   - `OAUTH_CLIENT_ID`: For ChatGPT integration (optional)
   - `OAUTH_CLIENT_SECRET`: For ChatGPT integration (optional)
   - `GITHUB_TOKEN`: For GitHub integration (optional)

3. **Access Your Instance**:
   - Web Interface: `https://your-domain.com`
   - API: `https://your-domain.com/api/v1`
   - Health Check: `https://your-domain.com/health`

### Option 2: Docker Compose

1. **Clone Repository**:
   ```bash
   git clone https://github.com/your-org/mcp-host.git
   cd mcp-host
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Deploy**:
   ```bash
   docker-compose up -d
   ```

4. **Access Services**:
   - Web Interface: http://localhost:3000
   - API: http://localhost:8000
   - Health: http://localhost:8000/health

## 🎯 Coolify Deployment

MCP Host is optimized for Coolify deployment with automatic SSL, monitoring, and scaling.

### Deployment Steps

1. **Add to Coolify**:
   - Go to your Coolify dashboard
   - Click "New Resource" → "Docker Compose"
   - Import from Git: `https://github.com/your-org/mcp-host`

2. **Environment Configuration**:
   ```bash
   # Required
   SECRET_KEY=your-random-secret-key-here

   # Optional - ChatGPT Integration
   OAUTH_CLIENT_ID=your-oauth-client-id
   OAUTH_CLIENT_SECRET=your-oauth-client-secret
   OAUTH_REDIRECT_URI=https://your-domain.com/auth/callback

   # Optional - GitHub Integration
   GITHUB_TOKEN=your-github-token

   # Production Settings
   ENVIRONMENT=production
   DEBUG=false
   LOG_LEVEL=INFO
   CORS_ORIGINS=https://your-domain.com
   ```

3. **Domain Configuration**:
   - Set your custom domain in Coolify
   - SSL will be automatically configured
   - Health checks will monitor all services

4. **Monitoring**:
   - View logs in Coolify dashboard
   - Monitor resource usage
   - Set up alerts for downtime

### Production Recommendations

- **Memory**: Minimum 2GB RAM
- **Storage**: 10GB for logs and MCP servers
- **CPU**: 2 cores recommended
- **SSL**: Let's Encrypt (automatic via Coolify)
- **Backups**: Enable for data persistence

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | JWT secret key | - | ✅ |
| `OAUTH_CLIENT_ID` | ChatGPT OAuth client ID | - | ❌ |
| `OAUTH_CLIENT_SECRET` | ChatGPT OAuth secret | - | ❌ |
| `GITHUB_TOKEN` | GitHub API token | - | ❌ |
| `DATABASE_URL` | Database connection | sqlite:///./data/mcp_host.db | ❌ |
| `CORS_ORIGINS` | Allowed origins | * | ❌ |
| `MAX_CONCURRENT_SERVERS` | Server limit | 10 | ❌ |
| `LOG_LEVEL` | Logging level | INFO | ❌ |

### Database Configuration

**SQLite (Default)**:
```bash
DATABASE_URL=sqlite:///./data/mcp_host.db
```

**PostgreSQL (Production)**:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/mcp_host
```

### OAuth2 Setup for ChatGPT

1. **Register Application** (with OpenAI when available)
2. **Configure Redirect URI**: `https://your-domain.com/auth/callback`
3. **Set Environment Variables**:
   ```bash
   OAUTH_CLIENT_ID=your-client-id
   OAUTH_CLIENT_SECRET=your-client-secret
   ```

## 💬 ChatGPT Integration

### Setting Up Custom Connector

1. **Deploy MCP Host** with OAuth2 configuration
2. **Get Connection Details**:
   - OAuth Authorization URL: `https://your-domain.com/auth/authorize`
   - Token URL: `https://your-domain.com/auth/token`
   - MCP Server URL: `https://your-domain.com/mcp`

3. **Configure in ChatGPT**:
   ```json
   {
     "name": "My MCP Host",
     "description": "Connect to my MCP servers",
     "mcp_server_url": "https://your-domain.com/mcp",
     "authentication": "oauth",
     "client_id": "your-client-id",
     "authorization_url": "https://your-domain.com/auth/authorize",
     "token_url": "https://your-domain.com/auth/token"
   }
   ```

### Testing ChatGPT Connection

1. **Add Test Server**:
   ```bash
   curl -X POST https://your-domain.com/api/v1/servers \
     -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "test-server",
       "command": "echo",
       "args": ["Hello from MCP Host!"],
       "transport_type": "stdio"
     }'
   ```

2. **Test in ChatGPT**:
   - Connect your custom connector
   - Try asking: "What tools are available?"
   - Test tool execution

## 🤖 Claude Integration

### Claude Desktop Configuration

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "mcp-host": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "https://your-domain.com/mcp",
        "-H", "Authorization: Bearer your-api-key",
        "-H", "Content-Type: application/json"
      ]
    }
  }
}
```

### API Integration

```python
import httpx

# Connect to MCP Host
client = httpx.Client(
    base_url="https://your-domain.com",
    headers={"Authorization": "Bearer your-api-key"}
)

# List available tools
tools = client.post("/mcp", json={
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
}).json()

print(tools)
```

## 📦 Adding MCP Servers

### From GitHub Repository

1. **Web Interface**:
   - Go to "Servers" → "Add Server"
   - Select "From GitHub"
   - Enter repository URL: `https://github.com/user/repo`
   - Configure and deploy

2. **API**:
   ```bash
   curl -X POST https://your-domain.com/api/v1/servers/from-github \
     -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
       "github_url": "https://github.com/czlonkowski/n8n-mcp",
       "name": "n8n-automation"
     }'
   ```

### Manual Configuration

```bash
curl -X POST https://your-domain.com/api/v1/servers \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-custom-server",
    "description": "Custom MCP server",
    "command": "python",
    "args": ["server.py"],
    "env": {
      "API_KEY": "secret"
    },
    "transport_type": "stdio",
    "auto_restart": true
  }'
```

### n8n Integration

1. **Quick Setup**:
   ```bash
   curl -X POST https://your-domain.com/api/v1/servers \
     -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "n8n-mcp",
       "command": "npx",
       "args": ["@n8n-mcp/server"],
       "env": {
         "N8N_API_URL": "http://your-n8n-instance:5678",
         "N8N_API_KEY": "your-n8n-api-key"
       },
       "transport_type": "stdio"
     }'
   ```

2. **Environment Variables**:
   - `N8N_API_URL`: Your n8n instance URL
   - `N8N_API_KEY`: n8n API key for authentication

## 📚 API Documentation

### Authentication

```bash
# API Key Authentication
curl -H "Authorization: Bearer your-api-key" \
  https://your-domain.com/api/v1/servers
```

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health check |
| `GET` | `/api/v1/servers` | List all servers |
| `POST` | `/api/v1/servers` | Create server |
| `GET` | `/api/v1/servers/{id}` | Get server details |
| `PUT` | `/api/v1/servers/{id}` | Update server |
| `DELETE` | `/api/v1/servers/{id}` | Delete server |
| `POST` | `/api/v1/servers/{id}/start` | Start server |
| `POST` | `/api/v1/servers/{id}/stop` | Stop server |

### MCP Protocol Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/mcp` | MCP JSON-RPC requests |
| `GET` | `/sse` | Server-Sent Events |
| `GET` | `/auth/authorize` | OAuth2 authorization |
| `POST` | `/auth/token` | OAuth2 token exchange |

### WebSocket Events

Connect to `wss://your-domain.com/ws` for real-time updates:

```javascript
const ws = new WebSocket('wss://your-domain.com/ws?token=your-api-key');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Server event:', data);
};
```

## 🔍 Troubleshooting

### Common Issues

**1. Server Won't Start**
```bash
# Check logs
docker-compose logs backend

# Common causes:
# - Missing SECRET_KEY
# - Port conflicts
# - Database connection issues
```

**2. ChatGPT Connection Failed**
```bash
# Verify OAuth2 configuration
curl https://your-domain.com/.well-known/oauth-authorization-server

# Check CORS settings
CORS_ORIGINS=https://chat.openai.com
```

**3. MCP Server Errors**
```bash
# Check server logs
curl https://your-domain.com/api/v1/servers/1/health

# Common fixes:
# - Verify command path
# - Check environment variables
# - Ensure dependencies are installed
```

**4. Permission Denied**
```bash
# Check API key permissions
curl -H "Authorization: Bearer your-key" \
  https://your-domain.com/api/v1/keys

# Verify user has required permissions
```

### Debug Mode

Enable debug logging:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

### Health Checks

```bash
# System health
curl https://your-domain.com/health

# Server health
curl https://your-domain.com/api/v1/servers/1/health

# OAuth2 metadata
curl https://your-domain.com/.well-known/oauth-authorization-server
```

### Support

- **Documentation**: [docs.mcphost.com](https://docs.mcphost.com)
- **Issues**: [GitHub Issues](https://github.com/your-org/mcp-host/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/mcp-host/discussions)
- **Discord**: [Community Discord](https://discord.gg/mcp-host)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. **Clone Repository**:
   ```bash
   git clone https://github.com/your-org/mcp-host.git
   cd mcp-host
   ```

2. **Backend Development**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python -m uvicorn src.server:app --reload
   ```

3. **Frontend Development**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Testing**:
   ```bash
   # Backend tests
   cd backend
   pytest

   # Frontend tests
   cd frontend
   npm test
   ```

### Release Process

1. Update version in `package.json` and `pyproject.toml`
2. Create release notes
3. Tag release: `git tag v1.0.0`
4. Push tags: `git push --tags`
5. GitHub Actions will build and release

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) - The foundation protocol
- [FastMCP](https://github.com/jlowin/fastmcp) - Python MCP framework
- [Coolify](https://coolify.io/) - Deployment platform
- [n8n](https://n8n.io/) - Workflow automation platform

---

<div align="center">

**[Website](https://mcphost.com)** • **[Documentation](https://docs.mcphost.com)** • **[Community](https://discord.gg/mcp-host)** • **[Support](https://github.com/your-org/mcp-host/issues)**

Made with ❤️ by the MCP Host Team

</div>