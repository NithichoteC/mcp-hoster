"""
n8n MCP Server Adapter
Converts n8n-mcp stdio server to HTTP/SSE for ChatGPT compatibility
"""
import os
import asyncio
import json
import subprocess
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

from ..models import MCPServer, TransportType, ServerStatus

class N8NAdapter:
    """Adapter for n8n-mcp server to convert stdio to HTTP/SSE"""

    def __init__(self):
        self.active_processes: Dict[str, subprocess.Popen] = {}

    async def create_n8n_server_config(
        self,
        name: str = "n8n-mcp",
        n8n_api_url: Optional[str] = None,
        n8n_api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create n8n MCP server configuration"""

        # Base command for n8n-mcp
        command = "npx"
        args = ["@n8n-mcp/server"]

        # Environment variables for n8n API
        env = {}
        if n8n_api_url:
            env["N8N_API_URL"] = n8n_api_url
        if n8n_api_key:
            env["N8N_API_KEY"] = n8n_api_key

        return {
            "name": name,
            "description": "n8n workflow automation MCP server - provides AI assistants with access to n8n node documentation and workflow management",
            "github_url": "https://github.com/czlonkowski/n8n-mcp",
            "command": command,
            "args": args,
            "env": env,
            "transport_type": TransportType.STDIO,
            "auto_restart": True,
            "health_check_interval": 60
        }

    async def start_n8n_stdio_server(self, config: Dict[str, Any]) -> subprocess.Popen:
        """Start n8n MCP server in stdio mode"""
        try:
            # Prepare command
            cmd = [config["command"]] + config["args"]
            env = {**os.environ, **config.get("env", {})}

            logger.info(f"Starting n8n-mcp server: {' '.join(cmd)}")

            # Start process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            # Test initial connection
            if await self._test_n8n_connection(process):
                logger.info("n8n-mcp server started successfully")
                return process
            else:
                process.kill()
                await process.wait()
                raise Exception("Failed to establish connection with n8n-mcp server")

        except Exception as e:
            logger.error(f"Failed to start n8n-mcp server: {e}")
            raise

    async def _test_n8n_connection(self, process: subprocess.Popen) -> bool:
        """Test connection to n8n MCP server"""
        try:
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mcp-host",
                        "version": "1.0.0"
                    }
                }
            }

            # Send request
            request_json = json.dumps(init_request) + "\n"
            process.stdin.write(request_json.encode())
            await process.stdin.drain()

            # Read response with timeout
            try:
                response_line = await asyncio.wait_for(
                    process.stdout.readline(),
                    timeout=10.0
                )
                response = json.loads(response_line.decode())

                # Check if it's a valid MCP response
                if response.get("jsonrpc") == "2.0" and "result" in response:
                    capabilities = response["result"].get("capabilities", {})
                    logger.info(f"n8n-mcp server capabilities: {capabilities}")
                    return True

            except asyncio.TimeoutError:
                logger.error("n8n-mcp server initialization timeout")
                return False

        except Exception as e:
            logger.error(f"n8n-mcp connection test failed: {e}")
            return False

        return False

    async def proxy_n8n_request(self, process: subprocess.Popen, method: str, params: Any = None) -> Dict[str, Any]:
        """Proxy request to n8n MCP server"""
        request_id = str(uuid.uuid4())

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }

        try:
            # Send request
            request_json = json.dumps(request) + "\n"
            process.stdin.write(request_json.encode())
            await process.stdin.drain()

            # Read response
            response_line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=30.0
            )

            response = json.loads(response_line.decode())
            return response

        except asyncio.TimeoutError:
            raise Exception(f"Request timeout for method: {method}")
        except Exception as e:
            raise Exception(f"Request failed for method {method}: {str(e)}")

    async def get_n8n_tools(self, process: subprocess.Popen) -> List[Dict[str, Any]]:
        """Get available tools from n8n MCP server"""
        try:
            response = await self.proxy_n8n_request(process, "tools/list")
            return response.get("result", [])
        except Exception as e:
            logger.error(f"Failed to get n8n tools: {e}")
            return []

    async def get_n8n_resources(self, process: subprocess.Popen) -> List[Dict[str, Any]]:
        """Get available resources from n8n MCP server"""
        try:
            response = await self.proxy_n8n_request(process, "resources/list")
            return response.get("result", [])
        except Exception as e:
            logger.error(f"Failed to get n8n resources: {e}")
            return []

    async def call_n8n_tool(self, process: subprocess.Popen, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific n8n tool"""
        try:
            params = {
                "name": tool_name,
                "arguments": arguments
            }
            response = await self.proxy_n8n_request(process, "tools/call", params)
            return response
        except Exception as e:
            logger.error(f"Failed to call n8n tool {tool_name}: {e}")
            raise

    async def read_n8n_resource(self, process: subprocess.Popen, uri: str) -> Dict[str, Any]:
        """Read a specific n8n resource"""
        try:
            params = {"uri": uri}
            response = await self.proxy_n8n_request(process, "resources/read", params)
            return response
        except Exception as e:
            logger.error(f"Failed to read n8n resource {uri}: {e}")
            raise

    async def stop_n8n_server(self, process: subprocess.Popen) -> bool:
        """Stop n8n MCP server"""
        try:
            if process and process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()

                logger.info("n8n-mcp server stopped")
                return True
            return True

        except Exception as e:
            logger.error(f"Failed to stop n8n-mcp server: {e}")
            return False

    def convert_to_sse_format(self, mcp_response: Dict[str, Any]) -> str:
        """Convert MCP response to SSE format for ChatGPT"""
        sse_data = {
            "id": mcp_response.get("id"),
            "type": "response",
            "data": mcp_response,
            "timestamp": datetime.utcnow().isoformat()
        }

        return f"data: {json.dumps(sse_data)}\n\n"

    def convert_to_openapi_schema(self, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert n8n MCP tools to OpenAPI schema for ChatGPT"""
        openapi_schema = {
            "openapi": "3.0.0",
            "info": {
                "title": "n8n MCP Server API",
                "version": "1.0.0",
                "description": "n8n workflow automation via MCP protocol"
            },
            "servers": [
                {
                    "url": "/mcp",
                    "description": "MCP Gateway"
                }
            ],
            "paths": {},
            "components": {
                "schemas": {},
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer"
                    }
                }
            },
            "security": [{"bearerAuth": []}]
        }

        # Convert each tool to OpenAPI path
        for tool in tools:
            tool_name = tool.get("name", "")
            description = tool.get("description", "")
            input_schema = tool.get("inputSchema", {})

            path = f"/tools/{tool_name}"
            openapi_schema["paths"][path] = {
                "post": {
                    "summary": description,
                    "description": description,
                    "operationId": f"call_{tool_name}",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": input_schema
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Tool execution result",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "result": {"type": "object"},
                                            "success": {"type": "boolean"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request"
                        },
                        "500": {
                            "description": "Server error"
                        }
                    }
                }
            }

        return openapi_schema

# Global n8n adapter instance
n8n_adapter = N8NAdapter()