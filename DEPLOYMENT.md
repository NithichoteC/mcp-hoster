# MCP Host Deployment Guide

This guide covers various deployment options for MCP Host, from development to production environments.

## 📋 Table of Contents

1. [Coolify Deployment (Recommended)](#coolify-deployment-recommended)
2. [Docker Compose](#docker-compose)
3. [Kubernetes](#kubernetes)
4. [Manual Installation](#manual-installation)
5. [Environment Configuration](#environment-configuration)
6. [SSL/TLS Setup](#ssltls-setup)
7. [Monitoring & Logging](#monitoring--logging)
8. [Backup & Recovery](#backup--recovery)
9. [Scaling](#scaling)
10. [Troubleshooting](#troubleshooting)

## 🚀 Coolify Deployment (Recommended)

Coolify provides the easiest deployment with automatic SSL, monitoring, and scaling.

### Prerequisites

- Coolify instance running
- Domain name configured
- Basic understanding of Docker containers

### Step-by-Step Deployment

1. **Access Coolify Dashboard**
   ```
   https://your-coolify-instance.com
   ```

2. **Create New Resource**
   - Click "New Resource"
   - Select "Docker Compose"
   - Choose "From Git Repository"

3. **Repository Configuration**
   ```
   Repository URL: https://github.com/your-org/mcp-host
   Branch: main
   Docker Compose Path: docker-compose.yml
   ```

4. **Environment Variables**
   ```bash
   # Required
   SECRET_KEY=your-very-secure-random-string-here-min-32-chars

   # ChatGPT Integration (Optional)
   OAUTH_CLIENT_ID=your-oauth-client-id
   OAUTH_CLIENT_SECRET=your-oauth-client-secret
   OAUTH_REDIRECT_URI=https://your-domain.com/auth/callback

   # GitHub Integration (Optional)
   GITHUB_TOKEN=ghp_your_github_personal_access_token

   # Production Settings
   ENVIRONMENT=production
   DEBUG=false
   LOG_LEVEL=INFO
   CORS_ORIGINS=https://your-domain.com
   ```

5. **Domain Configuration**
   - Add your domain: `your-domain.com`
   - Enable SSL (Let's Encrypt)
   - Set up DNS records

6. **Deploy**
   - Click "Deploy"
   - Monitor deployment logs
   - Verify health checks pass

### Coolify-Specific Features

- **Automatic SSL**: Let's Encrypt certificates
- **Health Monitoring**: Built-in health checks
- **Log Aggregation**: Centralized logging
- **Backup Management**: Scheduled backups
- **Zero-Downtime Deployments**: Rolling updates
- **Resource Monitoring**: CPU, memory, disk usage

## 🐳 Docker Compose

For self-managed deployments or development environments.

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 10GB disk space

### Quick Start

1. **Clone Repository**
   ```bash
   git clone https://github.com/your-org/mcp-host.git
   cd mcp-host
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   nano .env  # Configure your settings
   ```

3. **Deploy**
   ```bash
   # Development
   docker-compose up -d

   # Production
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

4. **Verify Deployment**
   ```bash
   # Check service status
   docker-compose ps

   # View logs
   docker-compose logs -f

   # Health check
   curl http://localhost:8000/health
   ```

### Production Configuration

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - LOG_LEVEL=INFO
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
      restart_policy:
        condition: on-failure
        max_attempts: 3

  frontend:
    environment:
      - NODE_ENV=production
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

  nginx:
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./ssl:/etc/nginx/ssl:ro
```

## ☸️ Kubernetes

For enterprise deployments requiring high availability and auto-scaling.

### Prerequisites

- Kubernetes cluster 1.20+
- kubectl configured
- Ingress controller (nginx/traefik)
- Cert-manager for SSL

### Deployment Manifests

1. **Namespace**
   ```yaml
   apiVersion: v1
   kind: Namespace
   metadata:
     name: mcp-host
   ```

2. **ConfigMap**
   ```yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: mcp-host-config
     namespace: mcp-host
   data:
     ENVIRONMENT: "production"
     DEBUG: "false"
     LOG_LEVEL: "INFO"
     CORS_ORIGINS: "https://your-domain.com"
   ```

3. **Secret**
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: mcp-host-secrets
     namespace: mcp-host
   type: Opaque
   data:
     SECRET_KEY: <base64-encoded-secret>
     OAUTH_CLIENT_SECRET: <base64-encoded-secret>
     GITHUB_TOKEN: <base64-encoded-token>
   ```

4. **Backend Deployment**
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: mcp-host-backend
     namespace: mcp-host
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: mcp-host-backend
     template:
       metadata:
         labels:
           app: mcp-host-backend
       spec:
         containers:
         - name: backend
           image: mcp-host-backend:latest
           ports:
           - containerPort: 8000
           envFrom:
           - configMapRef:
               name: mcp-host-config
           - secretRef:
               name: mcp-host-secrets
           resources:
             requests:
               memory: "512Mi"
               cpu: "250m"
             limits:
               memory: "2Gi"
               cpu: "1000m"
           livenessProbe:
             httpGet:
               path: /health
               port: 8000
             initialDelaySeconds: 30
             periodSeconds: 10
           readinessProbe:
             httpGet:
               path: /health
               port: 8000
             initialDelaySeconds: 5
             periodSeconds: 5
   ```

5. **Service & Ingress**
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: mcp-host-backend-service
     namespace: mcp-host
   spec:
     selector:
       app: mcp-host-backend
     ports:
     - port: 80
       targetPort: 8000
   ---
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: mcp-host-ingress
     namespace: mcp-host
     annotations:
       cert-manager.io/cluster-issuer: "letsencrypt-prod"
       nginx.ingress.kubernetes.io/rate-limit: "100"
   spec:
     tls:
     - hosts:
       - your-domain.com
       secretName: mcp-host-tls
     rules:
     - host: your-domain.com
       http:
         paths:
         - path: /
           pathType: Prefix
           backend:
             service:
               name: mcp-host-backend-service
               port:
                 number: 80
   ```

### Deployment Commands

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n mcp-host

# View logs
kubectl logs -f deployment/mcp-host-backend -n mcp-host

# Scale deployment
kubectl scale deployment mcp-host-backend --replicas=5 -n mcp-host
```

## 🛠️ Manual Installation

For development or custom deployment scenarios.

### Backend Setup

1. **System Requirements**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3.11 python3.11-venv nodejs npm git curl

   # CentOS/RHEL
   sudo yum install python3.11 python3.11-venv nodejs npm git curl
   ```

2. **Backend Installation**
   ```bash
   # Clone repository
   git clone https://github.com/your-org/mcp-host.git
   cd mcp-host/backend

   # Create virtual environment
   python3.11 -m venv venv
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt

   # Setup database
   alembic upgrade head

   # Create systemd service
   sudo cp scripts/mcp-host-backend.service /etc/systemd/system/
   sudo systemctl enable mcp-host-backend
   sudo systemctl start mcp-host-backend
   ```

3. **Frontend Installation**
   ```bash
   cd ../frontend

   # Install dependencies
   npm install

   # Build for production
   npm run build

   # Start with PM2
   npm install -g pm2
   pm2 start npm --name "mcp-host-frontend" -- start
   pm2 save
   pm2 startup
   ```

### Reverse Proxy Setup

1. **Nginx Configuration**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       return 301 https://$server_name$request_uri;
   }

   server {
       listen 443 ssl http2;
       server_name your-domain.com;

       ssl_certificate /path/to/ssl/cert.pem;
       ssl_certificate_key /path/to/ssl/key.pem;

       location /api/ {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       location / {
           proxy_pass http://localhost:3000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

## ⚙️ Environment Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | `your-32-char-random-string` |

### Optional Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection | `sqlite:///./data/mcp_host.db` |
| `HOST` | Server bind address | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |

### ChatGPT Integration

```bash
OAUTH_CLIENT_ID=your-openai-client-id
OAUTH_CLIENT_SECRET=your-openai-client-secret
OAUTH_REDIRECT_URI=https://your-domain.com/auth/callback
OAUTH_SCOPE=mcp:read mcp:write
```

### Database Configuration

**PostgreSQL (Recommended for Production)**:
```bash
DATABASE_URL=postgresql://user:password@host:5432/mcp_host
```

**MySQL**:
```bash
DATABASE_URL=mysql://user:password@host:3306/mcp_host
```

## 🔒 SSL/TLS Setup

### Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Custom Certificates

```bash
# Generate self-signed certificate (development only)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Use in nginx configuration
ssl_certificate /path/to/cert.pem;
ssl_certificate_key /path/to/key.pem;
```

## 📊 Monitoring & Logging

### Health Checks

```bash
# System health
curl https://your-domain.com/health

# Detailed metrics
curl https://your-domain.com/api/v1/metrics
```

### Log Configuration

**Structured Logging**:
```bash
LOG_FORMAT=json
LOG_LEVEL=INFO
```

**Log Rotation**:
```bash
# Logrotate configuration
/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 app app
}
```

### Prometheus Metrics

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'mcp-host'
    static_configs:
      - targets: ['your-domain.com:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

## 💾 Backup & Recovery

### Database Backup

**PostgreSQL**:
```bash
# Backup
pg_dump -h localhost -U user -d mcp_host > backup.sql

# Restore
psql -h localhost -U user -d mcp_host < backup.sql
```

**SQLite**:
```bash
# Backup
sqlite3 mcp_host.db ".backup backup.db"

# Restore
cp backup.db mcp_host.db
```

### Volume Backup

```bash
# Docker volumes
docker run --rm -v mcp_host_data:/data -v $(pwd):/backup busybox tar czf /backup/data-backup.tar.gz /data

# Kubernetes persistent volumes
kubectl exec deployment/mcp-host-backend -- tar czf - /app/data | gzip > data-backup.tar.gz
```

### Automated Backup Script

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Database backup
pg_dump -h localhost -U user -d mcp_host > $BACKUP_DIR/db_$DATE.sql

# Volume backup
tar czf $BACKUP_DIR/data_$DATE.tar.gz /app/data

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/ s3://your-backup-bucket/ --recursive
```

## 🚀 Scaling

### Horizontal Scaling

**Docker Compose**:
```bash
docker-compose up -d --scale backend=3 --scale frontend=2
```

**Kubernetes**:
```bash
kubectl scale deployment mcp-host-backend --replicas=5
kubectl scale deployment mcp-host-frontend --replicas=3
```

### Load Balancing

**Nginx Configuration**:
```nginx
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

upstream frontend {
    least_conn;
    server frontend1:3000;
    server frontend2:3000;
}
```

### Auto-Scaling (Kubernetes)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-host-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mcp-host-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## 🔧 Troubleshooting

### Common Issues

**1. Container Won't Start**
```bash
# Check logs
docker-compose logs backend
kubectl logs deployment/mcp-host-backend

# Common causes:
# - Missing environment variables
# - Port conflicts
# - Insufficient resources
```

**2. Database Connection Errors**
```bash
# Test database connection
docker-compose exec backend python -c "from src.database import engine; print(engine.execute('SELECT 1').scalar())"

# Check environment variables
echo $DATABASE_URL
```

**3. SSL Certificate Issues**
```bash
# Check certificate validity
openssl s509 -in cert.pem -text -noout

# Test SSL connection
openssl s_client -connect your-domain.com:443
```

**4. High Memory Usage**
```bash
# Monitor container resources
docker stats

# Check for memory leaks
kubectl top pods -n mcp-host
```

### Debug Mode

```bash
# Enable debug logging
DEBUG=true
LOG_LEVEL=DEBUG

# Development mode
ENVIRONMENT=development
```

### Performance Tuning

**Database Optimization**:
```sql
-- PostgreSQL
ANALYZE;
REINDEX DATABASE mcp_host;

-- Add indexes for frequently queried columns
CREATE INDEX idx_servers_status ON mcp_servers(status);
CREATE INDEX idx_sessions_active ON sessions(is_active);
```

**Container Resources**:
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

### Support Channels

- **Documentation**: https://docs.mcphost.com
- **GitHub Issues**: https://github.com/your-org/mcp-host/issues
- **Community Discord**: https://discord.gg/mcp-host
- **Professional Support**: support@mcphost.com

---

## 📚 Additional Resources

- [Configuration Reference](CONFIGURATION.md)
- [API Documentation](API.md)
- [Security Best Practices](SECURITY.md)
- [Performance Tuning](PERFORMANCE.md)
- [Migration Guide](MIGRATION.md)