# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Host is a professional gateway for the Model Context Protocol (MCP) that enables any AI agent (ChatGPT, Claude, custom applications) to connect to any MCP server. It acts as a universal proxy and management layer for MCP servers with multi-transport protocol support.

## Development Commands

### Backend (Python/FastAPI)
```bash
# Development setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run development server
python -m uvicorn src.server:app --reload --host 0.0.0.0 --port 8000

# Database migrations (if using Alembic)
alembic upgrade head

# Run with debug logging
DEBUG=true LOG_LEVEL=DEBUG python -m uvicorn src.server:app --reload
```

### Frontend (Next.js/React)
```bash
# Development setup
cd frontend
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check

# Linting
npm run lint
```

### Docker Development
```bash
# Build and run all services
docker-compose up -d

# Build specific service
docker-compose build backend
docker-compose build frontend

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Development with live reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Testing
```bash
# Backend tests (if pytest is configured)
cd backend
pytest

# Frontend tests (if configured)
cd frontend
npm test

# Integration tests
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/servers
```

## Architecture Overview

### Core Components

**Backend Architecture (FastAPI + FastMCP)**:
- `src/server.py` - Main FastAPI application with OAuth2 endpoints for ChatGPT integration
- `src/gateway.py` - Core MCP proxy logic with `MCPServerManager` and `MCPGateway` classes
- `src/auth.py` - OAuth2 and API key authentication for multiple client types
- `src/models.py` - SQLAlchemy models defining MCP servers, sessions, API keys
- `src/config.py` - Pydantic settings with environment variable management

**Transport Layer Architecture**:
The system supports 4 transport protocols for maximum compatibility:
- **STDIO**: Traditional subprocess-based MCP servers
- **HTTP**: RESTful API integration
- **SSE**: Server-Sent Events for ChatGPT custom connectors
- **Streamable HTTP**: Modern MCP 2025 specification

**MCP Server Management**:
- `MCPServerManager` handles lifecycle of individual MCP server processes
- `MCPGateway` routes requests to appropriate servers and aggregates responses
- Adapters in `src/adapters/` handle protocol conversion (stdio→HTTP/SSE)

### Key Design Patterns

**Multi-Transport Proxy Pattern**:
```
ChatGPT/Claude → OAuth2/API Auth → MCPGateway → MCPServerManager → Individual MCP Servers
                                      ↓
                                 [stdio|http|sse|streamable_http]
```

**Server Registry Pattern**:
- Database stores server configurations with transport type, auth, and health info
- `MCPServerManager` maintains active server processes and HTTP clients
- Health checks and auto-restart functionality for reliability

**Session Management**:
- Each AI client gets a session with connected server list
- Requests are routed based on session state and tool availability
- Support for aggregating tools/resources from multiple servers

### Frontend Architecture

**Next.js App Router Structure**:
- `app/page.tsx` - Main dashboard with server monitoring
- `lib/api.ts` - Axios-based API client with authentication
- `types/index.ts` - TypeScript definitions matching backend models
- React Query for server state management and real-time updates

## Configuration

### Environment Variables
Critical environment variables (see `.env.example`):
- `SECRET_KEY` - JWT signing key (required)
- `OAUTH_CLIENT_ID`/`OAUTH_CLIENT_SECRET` - ChatGPT integration
- `DATABASE_URL` - SQLite or PostgreSQL connection
- `GITHUB_TOKEN` - For GitHub repository integration

### Multi-Environment Support
- Development: SQLite database, debug logging, CORS=*
- Production: PostgreSQL, structured logging, specific CORS origins
- Docker: Container-optimized with health checks and volume persistence

## MCP Protocol Integration

### Server Registration
MCP servers are registered with:
- Command and arguments for execution
- Transport type (stdio/http/sse/streamable_http)
- Environment variables and authentication config
- Health check intervals and auto-restart settings

### Protocol Routing
The gateway automatically routes MCP JSON-RPC requests:
- `tools/list` - Aggregated from all connected servers
- `tools/call` - Routed to server providing the specific tool
- `resources/list` - Aggregated resource discovery
- Session-based server selection for stateful interactions

### ChatGPT Integration
OAuth2 flow specifically designed for ChatGPT custom connectors:
- Authorization endpoint: `/auth/authorize`
- Token endpoint: `/auth/token`
- MCP endpoint: `/mcp` (JSON-RPC) or `/sse` (Server-Sent Events)
- Well-known endpoint: `/.well-known/oauth-authorization-server`

## Deployment Targets

### Coolify (Primary)
- One-click deployment with `coolify.json` configuration
- Automatic SSL/TLS with Let's Encrypt
- Built-in monitoring and backup systems
- Environment variable management through Coolify UI

### Docker Compose
- Multi-service orchestration with nginx reverse proxy
- Health checks and restart policies
- Volume persistence for data and logs
- Production-ready with resource limits

### Manual Deployment
- Systemd service files for process management
- Nginx configuration for reverse proxy and SSL termination
- Database migration and backup procedures

## Integration Points

### GitHub Integration
- `src/adapters/github.py` automatically discovers MCP servers from repositories
- Analyzes package.json, requirements.txt, and Dockerfile for server type detection
- One-click installation from popular MCP server repositories

### n8n Integration
- `src/adapters/n8n.py` provides stdio→HTTP conversion for n8n-mcp server
- Special handling for n8n workflow automation and node documentation
- Environment variable injection for n8n API credentials

### Authentication Layers
- OAuth2 for ChatGPT custom connectors
- API keys for Claude Desktop and custom integrations
- Session-based authentication with JWT tokens
- Permission-based access control (mcp:read, mcp:write, admin)