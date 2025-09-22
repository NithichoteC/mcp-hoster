"""
MCP Gateway - Core proxy and routing logic for connecting multiple MCP servers
Supports multiple transport protocols and AI client compatibility
"""
import os
import asyncio
import json
import subprocess
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from fastapi import WebSocket, HTTPException
from fastapi.responses import StreamingResponse
from starlette.responses import Response
import httpx
import websockets
from loguru import logger
from sqlalchemy.orm import Session

from .models import MCPServer, ServerStatus, TransportType, RequestLog, Session as DBSession
from .config import settings

class MCPServerManager:
    """Manages individual MCP server instances"""

    def __init__(self):
        self.active_servers: Dict[int, Dict[str, Any]] = {}
        self.server_processes: Dict[int, subprocess.Popen] = {}
        self.http_clients: Dict[int, httpx.AsyncClient] = {}

    async def start_server(self, db: Session, server: MCPServer) -> bool:
        """Start an MCP server instance"""
        try:
            server_id = server.id
            logger.info(f"Starting MCP server: {server.name} (ID: {server_id})")

            if server.transport_type == TransportType.STDIO:
                return await self._start_stdio_server(db, server)
            elif server.transport_type in [TransportType.HTTP, TransportType.SSE, TransportType.STREAMABLE_HTTP]:
                return await self._start_http_server(db, server)
            else:
                logger.error(f"Unsupported transport type: {server.transport_type}")
                return False

        except Exception as e:
            logger.error(f"Failed to start server {server.name}: {e}")
            await self._update_server_status(db, server.id, ServerStatus.ERROR)
            return False

    async def _start_stdio_server(self, db: Session, server: MCPServer) -> bool:
        """Start STDIO-based MCP server"""
        try:
            # Prepare command and environment
            cmd = [server.command] + server.args
            env = {**os.environ, **server.env}

            # Start subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            self.server_processes[server.id] = process

            # Test server connectivity
            if await self._test_stdio_connection(process):
                self.active_servers[server.id] = {
                    "server": server,
                    "process": process,
                    "type": "stdio",
                    "started_at": datetime.utcnow()
                }
                await self._update_server_status(db, server.id, ServerStatus.ACTIVE)
                logger.info(f"STDIO server {server.name} started successfully")
                return True
            else:
                process.kill()
                await process.wait()
                return False

        except Exception as e:
            logger.error(f"Failed to start STDIO server {server.name}: {e}")
            return False

    async def _start_http_server(self, db: Session, server: MCPServer) -> bool:
        """Start HTTP/SSE/Streamable HTTP server"""
        try:
            # For HTTP servers, we assume they're already running
            # We just need to test connectivity
            base_url = f"http://{server.host}:{server.port}"
            client = httpx.AsyncClient(base_url=base_url, timeout=30.0)

            # Test connectivity
            if await self._test_http_connection(client, server):
                self.http_clients[server.id] = client
                self.active_servers[server.id] = {
                    "server": server,
                    "client": client,
                    "type": "http",
                    "base_url": base_url,
                    "started_at": datetime.utcnow()
                }
                await self._update_server_status(db, server.id, ServerStatus.ACTIVE)
                logger.info(f"HTTP server {server.name} connected successfully")
                return True
            else:
                await client.aclose()
                return False

        except Exception as e:
            logger.error(f"Failed to connect to HTTP server {server.name}: {e}")
            return False

    async def _test_stdio_connection(self, process: subprocess.Popen) -> bool:
        """Test STDIO server connection"""
        try:
            # Send simple ping request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "ping"
            }

            # Write request
            process.stdin.write(json.dumps(request).encode() + b'\n')
            await process.stdin.drain()

            # Read response with timeout
            try:
                response_line = await asyncio.wait_for(
                    process.stdout.readline(),
                    timeout=5.0
                )
                response = json.loads(response_line.decode())
                return "jsonrpc" in response
            except asyncio.TimeoutError:
                logger.warning("STDIO server ping timeout")
                return False

        except Exception as e:
            logger.error(f"STDIO connection test failed: {e}")
            return False

    async def _test_http_connection(self, client: httpx.AsyncClient, server: MCPServer) -> bool:
        """Test HTTP server connection"""
        try:
            # Try to get server capabilities
            if server.transport_type == TransportType.SSE:
                response = await client.get("/sse")
            elif server.transport_type == TransportType.STREAMABLE_HTTP:
                response = await client.get("/")
            else:
                response = await client.get("/health")

            return response.status_code in [200, 201, 202]

        except Exception as e:
            logger.error(f"HTTP connection test failed: {e}")
            return False

    async def stop_server(self, db: Session, server_id: int) -> bool:
        """Stop an MCP server instance"""
        try:
            if server_id not in self.active_servers:
                return True

            server_info = self.active_servers[server_id]
            logger.info(f"Stopping MCP server ID: {server_id}")

            if server_info["type"] == "stdio":
                process = server_info["process"]
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()

            elif server_info["type"] == "http":
                client = server_info["client"]
                await client.aclose()

            # Clean up
            self.active_servers.pop(server_id, None)
            self.server_processes.pop(server_id, None)
            self.http_clients.pop(server_id, None)

            await self._update_server_status(db, server_id, ServerStatus.INACTIVE)
            logger.info(f"Server {server_id} stopped successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to stop server {server_id}: {e}")
            return False

    async def proxy_request(self, server_id: int, method: str, params: Any = None) -> Dict[str, Any]:
        """Proxy a request to specific MCP server"""
        if server_id not in self.active_servers:
            raise HTTPException(status_code=404, detail="Server not found or inactive")

        server_info = self.active_servers[server_id]
        request_id = str(uuid.uuid4())

        request_data = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }

        start_time = time.time()

        try:
            if server_info["type"] == "stdio":
                return await self._proxy_stdio_request(server_info, request_data)
            elif server_info["type"] == "http":
                return await self._proxy_http_request(server_info, request_data)
            else:
                raise HTTPException(status_code=500, detail="Unsupported server type")

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Request proxy failed for server {server_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Server request failed: {str(e)}")

    async def _proxy_stdio_request(self, server_info: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Proxy request to STDIO server"""
        process = server_info["process"]

        # Send request
        request_json = json.dumps(request_data) + "\n"
        process.stdin.write(request_json.encode())
        await process.stdin.drain()

        # Read response
        response_line = await asyncio.wait_for(
            process.stdout.readline(),
            timeout=settings.server_timeout
        )

        response = json.loads(response_line.decode())
        return response

    async def _proxy_http_request(self, server_info: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Proxy request to HTTP server"""
        client = server_info["client"]
        server = server_info["server"]

        if server.transport_type == TransportType.SSE:
            # SSE transport
            response = await client.post("/sse", json=request_data)
        elif server.transport_type == TransportType.STREAMABLE_HTTP:
            # Streamable HTTP transport
            response = await client.post("/", json=request_data)
        else:
            # Regular HTTP
            response = await client.post("/mcp", json=request_data)

        response.raise_for_status()
        return response.json()

    async def _update_server_status(self, db: Session, server_id: int, status: ServerStatus):
        """Update server status in database"""
        server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
        if server:
            server.status = status
            server.last_health_check = datetime.utcnow()
            db.commit()

    async def get_server_capabilities(self, server_id: int) -> Dict[str, Any]:
        """Get capabilities from specific server"""
        try:
            response = await self.proxy_request(server_id, "initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {}
            })
            return response.get("result", {})
        except Exception as e:
            logger.error(f"Failed to get capabilities for server {server_id}: {e}")
            return {}

    async def health_check(self, db: Session, server_id: int) -> bool:
        """Perform health check on server"""
        try:
            if server_id not in self.active_servers:
                return False

            # Try to ping the server
            start_time = time.time()
            await self.proxy_request(server_id, "ping")
            response_time = int((time.time() - start_time) * 1000)

            # Update health check timestamp
            await self._update_server_status(db, server_id, ServerStatus.ACTIVE)
            return True

        except Exception as e:
            logger.error(f"Health check failed for server {server_id}: {e}")
            await self._update_server_status(db, server_id, ServerStatus.ERROR)
            return False

# Global server manager instance
server_manager = MCPServerManager()

class MCPGateway:
    """Main gateway for routing requests to appropriate MCP servers"""

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    async def create_session(self, db: Session, client_type: str, client_info: Dict[str, Any] = None) -> str:
        """Create a new client session"""
        session_id = str(uuid.uuid4())

        # Create database session
        db_session = DBSession(
            session_id=session_id,
            client_type=client_type,
            client_info=client_info or {},
            connected_servers=[],
            is_active=True
        )
        db.add(db_session)
        db.commit()

        # Create in-memory session
        self.sessions[session_id] = {
            "client_type": client_type,
            "client_info": client_info or {},
            "connected_servers": [],
            "created_at": datetime.utcnow()
        }

        logger.info(f"Created session {session_id} for {client_type}")
        return session_id

    async def route_request(self, session_id: str, method: str, params: Any = None) -> Dict[str, Any]:
        """Route request to appropriate server(s)"""
        if session_id not in self.sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        session = self.sessions[session_id]

        # Handle different routing strategies
        if method in ["tools/list", "resources/list", "prompts/list"]:
            # Aggregate from all connected servers
            return await self._aggregate_from_servers(session, method, params)
        elif method.startswith("tools/call"):
            # Route to specific server based on tool
            return await self._route_tool_call(session, method, params)
        else:
            # Route to primary server or first available
            return await self._route_to_primary_server(session, method, params)

    async def _aggregate_from_servers(self, session: Dict[str, Any], method: str, params: Any) -> Dict[str, Any]:
        """Aggregate results from multiple servers"""
        results = []
        connected_servers = session.get("connected_servers", [])

        for server_id in connected_servers:
            try:
                response = await server_manager.proxy_request(server_id, method, params)
                if "result" in response:
                    # Add server info to each item
                    server_result = response["result"]
                    if isinstance(server_result, list):
                        for item in server_result:
                            item["_server_id"] = server_id
                        results.extend(server_result)
                    elif isinstance(server_result, dict):
                        server_result["_server_id"] = server_id
                        results.append(server_result)

            except Exception as e:
                logger.error(f"Failed to get {method} from server {server_id}: {e}")
                continue

        return {
            "jsonrpc": "2.0",
            "id": params.get("id") if params else None,
            "result": results
        }

    async def _route_tool_call(self, session: Dict[str, Any], method: str, params: Any) -> Dict[str, Any]:
        """Route tool call to appropriate server"""
        # Extract tool name from params
        tool_name = params.get("name") if params else None
        if not tool_name:
            raise HTTPException(status_code=400, detail="Tool name required")

        # Find server that provides this tool
        connected_servers = session.get("connected_servers", [])
        for server_id in connected_servers:
            try:
                # Get tools list from server to check if it has the tool
                tools_response = await server_manager.proxy_request(server_id, "tools/list")
                tools = tools_response.get("result", [])

                for tool in tools:
                    if tool.get("name") == tool_name:
                        # Found the server, route the call
                        return await server_manager.proxy_request(server_id, method, params)

            except Exception as e:
                logger.error(f"Failed to check tools on server {server_id}: {e}")
                continue

        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    async def _route_to_primary_server(self, session: Dict[str, Any], method: str, params: Any) -> Dict[str, Any]:
        """Route to primary server (first connected server)"""
        connected_servers = session.get("connected_servers", [])
        if not connected_servers:
            raise HTTPException(status_code=400, detail="No servers connected to session")

        primary_server_id = connected_servers[0]
        return await server_manager.proxy_request(primary_server_id, method, params)

# Global gateway instance
gateway = MCPGateway()