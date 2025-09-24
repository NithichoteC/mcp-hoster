"""
Main MCP Host Server
Professional MCP gateway with FastMCP + FastAPI integration
Supports multiple AI clients: ChatGPT, Claude, API access
"""
import os
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, RedirectResponse
from fastapi.security import HTTPBearer
from starlette.responses import Response as StarletteResponse
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
import httpx

# FastMCP imports
from fastmcp import FastMCP

# Local imports
from .config import settings
from .database import init_db, get_db
from .models import (
    MCPServer, MCPServerCreate, MCPServerUpdate, MCPServerResponse,
    APIKey, APIKeyCreate, APIKeyResponse, HealthStatus, SystemStatus,
    ServerStatus, TransportType, AuthType
)
from .auth import (
    get_current_user, require_permission, create_access_token,
    create_refresh_token, create_authorization_code, verify_authorization_code,
    Token, AuthRequest, AuthCode, generate_api_key, hash_api_key
)
from .gateway import server_manager, gateway
from .adapters.n8n import N8NAdapter
from .adapters.github import GitHubAdapter

# Global state
startup_time = datetime.utcnow()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("🚀 Starting MCP Host Server...")

    try:
        # Initialize database
        print("📊 Initializing database...")
        init_db()
        print("✅ Database initialized")

        # Start background tasks with error handling
        print("🔄 Starting background tasks...")
        try:
            asyncio.create_task(health_check_loop())
            asyncio.create_task(cleanup_sessions_loop())
            print("✅ Background tasks started")
        except Exception as e:
            print(f"⚠️  Warning: Background tasks failed to start: {e}")

        print(f"✅ MCP Host Server started on http://{settings.host}:{settings.port}")

    except Exception as e:
        print(f"🚨 Critical error during startup: {e}")
        # Still yield to allow the app to start, but in degraded mode
        print("⚠️  Starting in degraded mode...")
    yield

    # Shutdown
    print("🛑 Shutting down MCP Host Server...")

    # Stop all active servers
    try:
        from .database import SessionLocal
        db = SessionLocal()
        try:
            active_servers = db.query(MCPServer).filter(MCPServer.status == ServerStatus.ACTIVE).all()
            for server in active_servers:
                try:
                    await server_manager.stop_server(db, server.id)
                except Exception as e:
                    print(f"⚠️  Failed to stop server {server.id}: {e}")
        finally:
            db.close()
    except Exception as e:
        print(f"⚠️  Error during server shutdown: {e}")

    print("✅ MCP Host Server shutdown complete")

# Initialize FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Professional MCP Host - Connect any MCP server to any AI agent",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Add session middleware for OAuth
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

# Security
security = HTTPBearer(auto_error=False)

# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with basic info"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "servers": "/api/v1/servers",
            "sessions": "/api/v1/sessions",
            "oauth": "/auth",
            "mcp": "/mcp"
        }
    }

@app.get("/health")
async def health_check():
    """Simple health check endpoint without database dependency"""
    try:
        uptime = (datetime.utcnow() - startup_time).total_seconds()
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": int(uptime),
            "service": "MCP Host Backend"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/status", response_model=SystemStatus)
async def system_status(db: Session = Depends(get_db)):
    """Detailed system status with database metrics (separate from health check)"""
    try:
        import psutil

        # Count servers by status (with error handling)
        try:
            total_servers = db.query(MCPServer).count()
            active_servers = db.query(MCPServer).filter(MCPServer.status == ServerStatus.ACTIVE).count()
            inactive_servers = db.query(MCPServer).filter(MCPServer.status == ServerStatus.INACTIVE).count()
            error_servers = db.query(MCPServer).filter(MCPServer.status == ServerStatus.ERROR).count()
        except Exception:
            total_servers = active_servers = inactive_servers = error_servers = 0

        # Count sessions (with error handling)
        try:
            from .models import Session as DBSession
            total_sessions = db.query(DBSession).count()
            active_sessions = db.query(DBSession).filter(DBSession.is_active == True).count()
        except Exception:
            total_sessions = active_sessions = 0

        # System metrics
        uptime = (datetime.utcnow() - startup_time).total_seconds()
        try:
            memory_info = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()
            memory_usage_mb = memory_info.used / 1024 / 1024
        except Exception:
            memory_usage_mb = 0.0
            cpu_percent = 0.0

        return SystemStatus(
            total_servers=total_servers,
            active_servers=active_servers,
            inactive_servers=inactive_servers,
            error_servers=error_servers,
            total_sessions=total_sessions,
            active_sessions=active_sessions,
            uptime_seconds=int(uptime),
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_percent
        )
    except Exception as e:
        # Return empty status if everything fails
        return SystemStatus(
            total_servers=0, active_servers=0, inactive_servers=0, error_servers=0,
            total_sessions=0, active_sessions=0, uptime_seconds=0,
            memory_usage_mb=0.0, cpu_usage_percent=0.0
        )

# ============================================================================
# OAUTH2 ENDPOINTS FOR CHATGPT INTEGRATION
# ============================================================================

@app.get("/auth/authorize")
async def oauth_authorize(
    request: Request,
    client_id: str,
    redirect_uri: str,
    response_type: str = "code",
    scope: Optional[str] = None,
    state: Optional[str] = None
):
    """OAuth2 authorization endpoint"""
    if response_type != "code":
        raise HTTPException(status_code=400, detail="Only authorization code flow supported")

    # For demo purposes, auto-approve. In production, show consent screen
    code = create_authorization_code(client_id, redirect_uri, scope)

    # Build redirect URL
    redirect_url = f"{redirect_uri}?code={code}"
    if state:
        redirect_url += f"&state={state}"

    return RedirectResponse(url=redirect_url)

@app.post("/auth/token", response_model=Token)
async def oauth_token(
    grant_type: str,
    code: Optional[str] = None,
    client_id: Optional[str] = None,
    redirect_uri: Optional[str] = None,
    refresh_token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """OAuth2 token endpoint"""
    if grant_type == "authorization_code":
        if not all([code, client_id, redirect_uri]):
            raise HTTPException(status_code=400, detail="Missing required parameters")

        # Verify authorization code
        code_data = verify_authorization_code(code, client_id, redirect_uri)
        if not code_data:
            raise HTTPException(status_code=400, detail="Invalid authorization code")

        # Create session
        session_id = await gateway.create_session(db, "chatgpt", {"client_id": client_id})

        # Create tokens
        access_token = create_access_token({
            "sub": client_id,
            "scope": code_data.get("scope", settings.oauth_scope),
            "session_id": session_id
        })

        refresh_token_str = create_refresh_token({
            "sub": client_id,
            "session_id": session_id
        })

        return Token(
            access_token=access_token,
            refresh_token=refresh_token_str,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            scope=code_data.get("scope", settings.oauth_scope)
        )

    elif grant_type == "refresh_token":
        # Handle refresh token flow
        raise HTTPException(status_code=501, detail="Refresh token flow not implemented")

    else:
        raise HTTPException(status_code=400, detail="Unsupported grant type")

@app.get("/.well-known/oauth-authorization-server")
async def oauth_metadata():
    """OAuth2 server metadata endpoint"""
    base_url = f"http://{settings.host}:{settings.port}"
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/auth/authorize",
        "token_endpoint": f"{base_url}/auth/token",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "scopes_supported": ["mcp:read", "mcp:write"],
        "token_endpoint_auth_methods_supported": ["client_secret_post"]
    }

# ============================================================================
# MCP SERVER MANAGEMENT API
# ============================================================================

@app.get("/api/v1/servers", response_model=List[MCPServerResponse])
async def list_servers(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission("mcp:read"))
):
    """List all MCP servers"""
    servers = db.query(MCPServer).all()
    return servers

@app.post("/api/v1/servers", response_model=MCPServerResponse)
async def create_server(
    server_data: MCPServerCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission("mcp:write"))
):
    """Create a new MCP server"""
    # Check if server name already exists
    existing = db.query(MCPServer).filter(MCPServer.name == server_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Server name already exists")

    # Create server
    server = MCPServer(**server_data.model_dump())
    db.add(server)
    db.commit()
    db.refresh(server)

    # Auto-start if configured
    if server.auto_restart:
        await server_manager.start_server(db, server)

    return server

@app.get("/api/v1/servers/{server_id}", response_model=MCPServerResponse)
async def get_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission("mcp:read"))
):
    """Get specific server details"""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server

@app.put("/api/v1/servers/{server_id}", response_model=MCPServerResponse)
async def update_server(
    server_id: int,
    server_data: MCPServerUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission("mcp:write"))
):
    """Update server configuration"""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    # Update fields
    for field, value in server_data.model_dump(exclude_unset=True).items():
        setattr(server, field, value)

    server.updated_at = datetime.utcnow()
    db.commit()

    # Restart server if it's running
    if server.status == ServerStatus.ACTIVE:
        await server_manager.stop_server(db, server_id)
        await server_manager.start_server(db, server)

    return server

@app.delete("/api/v1/servers/{server_id}")
async def delete_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission("mcp:write"))
):
    """Delete server"""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    # Stop server if running
    await server_manager.stop_server(db, server_id)

    # Delete from database
    db.delete(server)
    db.commit()

    return {"message": "Server deleted successfully"}

@app.post("/api/v1/servers/{server_id}/start")
async def start_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission("mcp:write"))
):
    """Start a server"""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    success = await server_manager.start_server(db, server)
    if success:
        return {"message": "Server started successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to start server")

@app.post("/api/v1/servers/{server_id}/stop")
async def stop_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission("mcp:write"))
):
    """Stop a server"""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    success = await server_manager.stop_server(db, server_id)
    if success:
        return {"message": "Server stopped successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to stop server")

@app.get("/api/v1/servers/{server_id}/health", response_model=HealthStatus)
async def check_server_health(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission("mcp:read"))
):
    """Check server health"""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    import time
    start_time = time.time()

    try:
        is_healthy = await server_manager.health_check(db, server_id)
        response_time = int((time.time() - start_time) * 1000)

        if is_healthy:
            # Get capabilities to count tools/resources
            capabilities = await server_manager.get_server_capabilities(server_id)
            tools_count = len(capabilities.get("tools", []))
            resources_count = len(capabilities.get("resources", []))

            return HealthStatus(
                server_id=server_id,
                status=ServerStatus.ACTIVE,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                tools_count=tools_count,
                resources_count=resources_count
            )
        else:
            return HealthStatus(
                server_id=server_id,
                status=ServerStatus.ERROR,
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                error="Health check failed"
            )

    except Exception as e:
        return HealthStatus(
            server_id=server_id,
            status=ServerStatus.ERROR,
            last_check=datetime.utcnow(),
            error=str(e)
        )

# ============================================================================
# MCP PROTOCOL ENDPOINTS (SSE & HTTP)
# ============================================================================

@app.api_route("/mcp", methods=["GET", "POST"])
@app.api_route("/sse", methods=["GET", "POST"])
async def mcp_endpoint(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Main MCP protocol endpoint (HTTP & SSE)"""
    if request.method == "GET":
        # SSE connection for ChatGPT
        return await handle_sse_connection(request, current_user)
    else:
        # HTTP POST for requests
        return await handle_mcp_request(request, current_user)

async def handle_sse_connection(request: Request, current_user: Dict[str, Any]):
    """Handle SSE connection for ChatGPT"""
    async def event_stream():
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connected', 'timestamp': datetime.utcnow().isoformat()})}\n\n"

        # Keep connection alive
        while True:
            try:
                # Send heartbeat every 30 seconds
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
                await asyncio.sleep(30)
            except Exception as e:
                break

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

async def handle_mcp_request(request: Request, current_user: Dict[str, Any]):
    """Handle MCP JSON-RPC requests"""
    try:
        # Parse request
        request_data = await request.json()

        # Get or create session
        session_id = current_user.get("session_id")
        if not session_id:
            db = next(get_db())
            session_id = await gateway.create_session(
                db,
                current_user.get("type", "api"),
                current_user
            )

        # Route request through gateway
        response = await gateway.route_request(
            session_id,
            request_data.get("method"),
            request_data.get("params")
        )

        return JSONResponse(content=response)

    except Exception as e:
        error_response = {
            "jsonrpc": "2.0",
            "id": request_data.get("id") if 'request_data' in locals() else None,
            "error": {
                "code": -32000,
                "message": str(e)
            }
        }
        return JSONResponse(content=error_response, status_code=500)

# ============================================================================
# API KEY MANAGEMENT
# ============================================================================

@app.get("/api/v1/keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission("admin"))
):
    """List all API keys"""
    keys = db.query(APIKey).filter(APIKey.is_active == True).all()
    return keys

@app.post("/api/v1/keys")
async def create_api_key(
    key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission("admin"))
):
    """Create a new API key"""
    # Generate key
    api_key = f"mcp_{generate_api_key()}"
    key_hash = hash_api_key(api_key)

    # Create database record
    db_key = APIKey(
        name=key_data.name,
        key_hash=key_hash,
        permissions=key_data.permissions,
        expires_at=key_data.expires_at
    )
    db.add(db_key)
    db.commit()
    db.refresh(db_key)

    # Return key (only time it's shown)
    return {
        "id": db_key.id,
        "name": db_key.name,
        "api_key": api_key,  # Only returned on creation
        "permissions": db_key.permissions,
        "created_at": db_key.created_at,
        "expires_at": db_key.expires_at
    }

# ============================================================================
# GITHUB INTEGRATION
# ============================================================================

@app.post("/api/v1/servers/from-github")
async def create_server_from_github(
    github_url: str,
    name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_permission("mcp:write"))
):
    """Create server from GitHub repository"""
    try:
        adapter = GitHubAdapter()
        server_config = await adapter.analyze_repository(github_url)

        # Create server
        server_data = MCPServerCreate(
            name=name or server_config["name"],
            description=server_config.get("description"),
            github_url=github_url,
            command=server_config["command"],
            args=server_config.get("args", []),
            env=server_config.get("env", {}),
            transport_type=TransportType.STDIO
        )

        return await create_server(server_data, db, current_user)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create server from GitHub: {str(e)}")

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def health_check_loop():
    """Background task for health checking servers"""
    while True:
        try:
            db = next(get_db())
            active_servers = db.query(MCPServer).filter(MCPServer.status == ServerStatus.ACTIVE).all()

            for server in active_servers:
                # Check if health check is due
                if (not server.last_health_check or
                    datetime.utcnow() - server.last_health_check > timedelta(seconds=server.health_check_interval)):

                    await server_manager.health_check(db, server.id)

            await asyncio.sleep(30)  # Check every 30 seconds

        except Exception as e:
            print(f"Health check error: {e}")
            await asyncio.sleep(30)

async def cleanup_sessions_loop():
    """Background task for cleaning up inactive sessions"""
    while True:
        try:
            db = next(get_db())
            from .models import Session as DBSession

            # Mark sessions inactive after 1 hour of inactivity
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            inactive_sessions = db.query(DBSession).filter(
                DBSession.last_activity < cutoff_time,
                DBSession.is_active == True
            ).all()

            for session in inactive_sessions:
                session.is_active = False
                # Clean up from gateway memory
                gateway.sessions.pop(session.session_id, None)

            db.commit()
            await asyncio.sleep(3600)  # Clean up every hour

        except Exception as e:
            print(f"Session cleanup error: {e}")
            await asyncio.sleep(3600)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "timestamp": datetime.utcnow().isoformat()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "timestamp": datetime.utcnow().isoformat()}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )