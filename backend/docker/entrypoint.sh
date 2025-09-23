#!/bin/bash
set -e

echo "🚀 Starting MCP Host Backend..."

# Wait for database to be ready (if using external DB)
if [[ "${DATABASE_URL}" == postgresql* ]]; then
    echo "⏳ Waiting for PostgreSQL to be ready..."
    until python -c "import psycopg2; psycopg2.connect('${DATABASE_URL}')" 2>/dev/null; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 2
    done
    echo "✅ PostgreSQL is ready!"
fi

# Data directories already created in Dockerfile
# Ensure proper ownership
chown -R mcphost:mcphost /app/data /app/logs /app/mcp_servers 2>/dev/null || true

# Run database migrations
echo "🔄 Running database migrations..."
if command -v alembic &> /dev/null; then
    alembic upgrade head
else
    echo "⚠️  Alembic not found, creating tables directly..."
    cd /app && python -c "from src.database import init_db; init_db()" || echo "⚠️  Database initialization failed"
fi

# Install default MCP servers if directory is empty
if [ ! "$(ls -A /app/mcp_servers)" ]; then
    echo "📦 Installing default MCP servers..."

    # Install n8n-mcp server
    cd /app/mcp_servers
    if npm init -y; then
        npm install @n8n-mcp/server || echo "⚠️  Failed to install n8n-mcp server"
    else
        echo "⚠️  Failed to initialize npm in mcp_servers directory"
    fi

    cd /app
fi

# Set up log rotation
if [ ! -f /app/logs/app.log ]; then
    touch /app/logs/app.log
fi

# Generate secret key if not provided
if [ -z "${SECRET_KEY}" ]; then
    export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
    echo "⚠️  Generated random SECRET_KEY. Set SECRET_KEY environment variable for production."
fi

# Start the application
echo "✅ Starting MCP Host Backend on port ${PORT:-8000}..."

# Execute the main command
exec "$@"