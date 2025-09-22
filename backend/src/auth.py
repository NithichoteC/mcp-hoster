"""
Authentication and authorization for MCP Host
Supports OAuth2 for ChatGPT integration and API keys for other clients
"""
import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2AuthorizationCodeBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from authlib.integrations.starlette_client import OAuth
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .config import settings
from .models import APIKey, Session as DBSession
from .database import get_db

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# OAuth2 setup for ChatGPT
oauth = OAuth()
oauth.register(
    name='mcp_host',
    client_id=settings.oauth_client_id,
    client_secret=settings.oauth_client_secret,
    authorize_url=f"http://{settings.host}:{settings.port}/auth/authorize",
    token_url=f"http://{settings.host}:{settings.port}/auth/token",
    redirect_uri=settings.oauth_redirect_uri,
)

# Token models
class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    scope: Optional[str] = None

class TokenData(BaseModel):
    client_id: Optional[str] = None
    scope: Optional[str] = None
    session_id: Optional[str] = None

class AuthRequest(BaseModel):
    client_id: str
    redirect_uri: str
    response_type: str = "code"
    scope: Optional[str] = None
    state: Optional[str] = None

class AuthCode(BaseModel):
    code: str
    client_id: str
    redirect_uri: str

# Utility functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT refresh token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt

def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        client_id: str = payload.get("sub")
        scope: str = payload.get("scope")
        session_id: str = payload.get("session_id")

        if client_id is None:
            return None

        return TokenData(client_id=client_id, scope=scope, session_id=session_id)
    except JWTError:
        return None

def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def generate_api_key() -> str:
    """Generate a new API key"""
    return secrets.token_urlsafe(32)

def verify_api_key(db: Session, api_key: str) -> Optional[APIKey]:
    """Verify API key and return key object if valid"""
    key_hash = hash_api_key(api_key)
    db_key = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active == True
    ).first()

    if db_key:
        # Check if key has expired
        if db_key.expires_at and db_key.expires_at < datetime.utcnow():
            return None

        # Update last used timestamp
        db_key.last_used = datetime.utcnow()
        db.commit()

    return db_key

def create_session(db: Session, client_type: str, client_info: Dict[str, Any] = None) -> DBSession:
    """Create a new session"""
    session_id = secrets.token_urlsafe(32)
    db_session = DBSession(
        session_id=session_id,
        client_type=client_type,
        client_info=client_info or {},
        connected_servers=[],
        is_active=True
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

# Dependency functions
async def get_current_user_oauth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[TokenData]:
    """Get current user from OAuth token"""
    if not credentials:
        return None

    token_data = verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data

async def get_current_user_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[APIKey]:
    """Get current user from API key"""
    if not credentials:
        return None

    # Check if it's an API key (different format than JWT)
    if not credentials.credentials.startswith("mcp_"):
        return None

    api_key = verify_api_key(db, credentials.credentials)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return api_key

async def get_current_user(
    oauth_user: Optional[TokenData] = Depends(get_current_user_oauth),
    api_key_user: Optional[APIKey] = Depends(get_current_user_api_key)
) -> Dict[str, Any]:
    """Get current user from either OAuth or API key"""
    if oauth_user:
        return {
            "type": "oauth",
            "client_id": oauth_user.client_id,
            "scope": oauth_user.scope,
            "session_id": oauth_user.session_id
        }
    elif api_key_user:
        return {
            "type": "api_key",
            "key_id": api_key_user.id,
            "name": api_key_user.name,
            "permissions": api_key_user.permissions
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_permission(permission: str):
    """Dependency factory for requiring specific permissions"""
    async def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ):
        if current_user["type"] == "oauth":
            # OAuth users have access based on scope
            scope = current_user.get("scope", "")
            if permission not in scope:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )
        elif current_user["type"] == "api_key":
            # API key users have access based on permissions
            permissions = current_user.get("permissions", [])
            if permission not in permissions and "admin" not in permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )

        return current_user

    return permission_checker

# OAuth2 authorization code storage (in production, use Redis)
authorization_codes: Dict[str, Dict[str, Any]] = {}

def create_authorization_code(client_id: str, redirect_uri: str, scope: str = None) -> str:
    """Create authorization code for OAuth flow"""
    code = secrets.token_urlsafe(32)
    authorization_codes[code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "created_at": datetime.utcnow(),
        "used": False
    }
    return code

def verify_authorization_code(code: str, client_id: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
    """Verify authorization code and return code data"""
    code_data = authorization_codes.get(code)
    if not code_data:
        return None

    # Check if already used
    if code_data["used"]:
        return None

    # Check if expired (codes expire after 10 minutes)
    if datetime.utcnow() - code_data["created_at"] > timedelta(minutes=10):
        del authorization_codes[code]
        return None

    # Check client_id and redirect_uri match
    if code_data["client_id"] != client_id or code_data["redirect_uri"] != redirect_uri:
        return None

    # Mark as used
    code_data["used"] = True

    return code_data