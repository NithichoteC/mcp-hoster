"""
Configuration management for MCP Host
"""
import os
from pathlib import Path
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application settings
    app_name: str = "MCP Host"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    # Database settings
    database_url: str = "sqlite:///./mcp_host.db"

    # Authentication settings
    secret_key: str = Field(default_factory=lambda: os.urandom(32).hex())
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # OAuth2 settings for ChatGPT integration
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    oauth_redirect_uri: str = "http://localhost:8000/auth/callback"
    oauth_scope: str = "mcp:read mcp:write"

    # CORS settings
    cors_origins: List[str] = ["*"]
    cors_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_headers: List[str] = ["*"]

    # MCP Server Registry
    mcp_servers_dir: str = "./mcp_servers"
    auto_discover_github: bool = True

    # GitHub settings
    github_token: Optional[str] = None

    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Performance settings
    max_concurrent_servers: int = 10
    server_timeout: int = 30
    connection_pool_size: int = 20

    # Security settings
    rate_limit_per_minute: int = 60
    max_request_size: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Ensure required directories exist
Path(settings.mcp_servers_dir).mkdir(parents=True, exist_ok=True)