"""
Database models for MCP Host
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from pydantic import BaseModel
from enum import Enum

Base = declarative_base()

class ServerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"

class TransportType(str, Enum):
    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"
    STREAMABLE_HTTP = "streamable_http"

class AuthType(str, Enum):
    NONE = "none"
    OAUTH = "oauth"
    API_KEY = "api_key"
    BEARER = "bearer"

# Database Models
class MCPServer(Base):
    __tablename__ = "mcp_servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    github_url = Column(String, nullable=True)
    command = Column(String, nullable=False)
    args = Column(JSON, default=list)
    env = Column(JSON, default=dict)
    transport_type = Column(String, default=TransportType.STDIO)
    host = Column(String, default="localhost")
    port = Column(Integer, nullable=True)
    status = Column(String, default=ServerStatus.INACTIVE)
    auth_type = Column(String, default=AuthType.NONE)
    auth_config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_health_check = Column(DateTime, nullable=True)
    health_check_interval = Column(Integer, default=60)  # seconds
    auto_restart = Column(Boolean, default=True)
    max_restarts = Column(Integer, default=3)
    restart_count = Column(Integer, default=0)

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    key_hash = Column(String, unique=True, index=True, nullable=False)
    permissions = Column(JSON, default=list)  # List of allowed actions
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    client_type = Column(String, nullable=False)  # "chatgpt", "claude", "api"
    client_info = Column(JSON, default=dict)
    connected_servers = Column(JSON, default=list)  # List of server IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=True)
    server_id = Column(Integer, nullable=True)
    method = Column(String, nullable=False)
    path = Column(String, nullable=False)
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    status_code = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic Models for API
class MCPServerCreate(BaseModel):
    name: str
    description: Optional[str] = None
    github_url: Optional[str] = None
    command: str
    args: list = []
    env: dict = {}
    transport_type: TransportType = TransportType.STDIO
    host: str = "localhost"
    port: Optional[int] = None
    auth_type: AuthType = AuthType.NONE
    auth_config: dict = {}
    auto_restart: bool = True
    max_restarts: int = 3
    health_check_interval: int = 60

class MCPServerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    command: Optional[str] = None
    args: Optional[list] = None
    env: Optional[dict] = None
    transport_type: Optional[TransportType] = None
    host: Optional[str] = None
    port: Optional[int] = None
    auth_type: Optional[AuthType] = None
    auth_config: Optional[dict] = None
    auto_restart: Optional[bool] = None
    max_restarts: Optional[int] = None
    health_check_interval: Optional[int] = None

class MCPServerResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    github_url: Optional[str]
    command: str
    args: list
    env: dict
    transport_type: TransportType
    host: str
    port: Optional[int]
    status: ServerStatus
    auth_type: AuthType
    auth_config: dict
    created_at: datetime
    updated_at: datetime
    last_health_check: Optional[datetime]
    health_check_interval: int
    auto_restart: bool
    max_restarts: int
    restart_count: int

    class Config:
        from_attributes = True

class APIKeyCreate(BaseModel):
    name: str
    permissions: list = []
    expires_at: Optional[datetime] = None

class APIKeyResponse(BaseModel):
    id: int
    name: str
    permissions: list
    created_at: datetime
    last_used: Optional[datetime]
    is_active: bool
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True

class HealthStatus(BaseModel):
    server_id: int
    status: ServerStatus
    last_check: datetime
    response_time_ms: Optional[int]
    error: Optional[str]
    tools_count: Optional[int]
    resources_count: Optional[int]

class SystemStatus(BaseModel):
    total_servers: int
    active_servers: int
    inactive_servers: int
    error_servers: int
    total_sessions: int
    active_sessions: int
    uptime_seconds: int
    memory_usage_mb: float
    cpu_usage_percent: float