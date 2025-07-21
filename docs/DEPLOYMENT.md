# HealthTwin AI - Deployment Guide

This guide covers various deployment options for the HealthTwin AI platform.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Security Considerations](#security-considerations)
7. [Monitoring and Logging](#monitoring-and-logging)

## Local Development

### Prerequisites

- Python 3.8+
- Node.js 16+
- Git

### Setup Steps

1. **Clone and Setup**
   ```bash
   git clone https://github.com/yourusername/Healthtwin-AI.git
   cd Healthtwin-AI
   
   # Backend setup
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Frontend setup
   cd frontend
   npm install
   cd ..
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Database Setup**
   ```bash
   python migrate_database.py
   ```

4. **Start Services**
   ```bash
   # Terminal 1: Backend
   python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   
   # Terminal 2: Frontend
   cd frontend && npm start
   ```

## Docker Deployment

### Single Container (Development)

```bash
# Backend only
docker build -f docker/Dockerfile.backend -t healthtwin-backend .
docker run -p 8000:8000 -v $(pwd)/uploads:/app/uploads healthtwin-backend

# Frontend only
docker build -f docker/Dockerfile.frontend -t healthtwin-frontend ./frontend
docker run -p 3000:3000 healthtwin-frontend
```

### Multi-Container with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Production Deployment

### Server Requirements

**Minimum:**
- 2 CPU cores
- 4GB RAM
- 20GB storage
- Ubuntu 20.04+ or CentOS 8+

**Recommended:**
- 4 CPU cores
- 8GB RAM
- 50GB SSD storage
- Load balancer for high availability

### Production Setup

1. **Server Preparation**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install dependencies
   sudo apt install -y python3 python3-pip nodejs npm nginx certbot
   
   # Install Docker (optional)
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```

2. **Application Deployment**
   ```bash
   # Clone repository
   git clone https://github.com/yourusername/Healthtwin-AI.git
   cd Healthtwin-AI
   
   # Setup Python environment
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Build frontend
   cd frontend
   npm install
   npm run build
   cd ..
   ```

3. **Systemd Service Setup**
   
   Create `/etc/systemd/system/healthtwin-backend.service`:
   ```ini
   [Unit]
   Description=HealthTwin Backend
   After=network.target
   
   [Service]
   Type=exec
   User=www-data
   Group=www-data
   WorkingDirectory=/opt/healthtwin-ai
   Environment=PATH=/opt/healthtwin-ai/venv/bin
   ExecStart=/opt/healthtwin-ai/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

4. **Nginx Configuration**
   
   Create `/etc/nginx/sites-available/healthtwin`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       # Frontend
       location / {
           root /opt/healthtwin-ai/frontend/build;
           try_files $uri $uri/ /index.html;
       }
       
       # Backend API
       location /api/ {
           proxy_pass http://127.0.0.1:8000/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       
       # Static files
       location /uploads/ {
           alias /opt/healthtwin-ai/uploads/;
           expires 1y;
           add_header Cache-Control "public, immutable";
       }
   }
   ```

5. **SSL Certificate**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

6. **Start Services**
   ```bash
   sudo systemctl enable healthtwin-backend
   sudo systemctl start healthtwin-backend
   sudo systemctl enable nginx
   sudo systemctl restart nginx
   ```

## Cloud Deployment

### AWS Deployment

#### Using EC2

1. **Launch EC2 Instance**
   - AMI: Ubuntu 20.04 LTS
   - Instance Type: t3.medium (minimum)
   - Security Groups: HTTP (80), HTTPS (443), SSH (22)

2. **Setup Application**
   ```bash
   # Connect to instance
   ssh -i your-key.pem ubuntu@your-instance-ip
   
   # Follow production setup steps above
   ```

#### Using AWS App Runner

1. **Create apprunner.yaml**
   ```yaml
   version: 1.0
   runtime: python3
   build:
     commands:
       build:
         - pip install -r requirements.txt
   run:
     runtime-version: 3.8
     command: uvicorn app.main:app --host 0.0.0.0 --port 8000
     network:
       port: 8000
       env: PORT
   ```

### Google Cloud Platform

#### Using Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/healthtwin-backend
gcloud run deploy --image gcr.io/PROJECT-ID/healthtwin-backend --platform managed
```

### Microsoft Azure

#### Using Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name healthtwin-backend \
  --image healthtwin-backend:latest \
  --ports 8000
```

## Environment Configuration

### Production Environment Variables

```env
# Security
SECRET_KEY=your-super-secret-key-here-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql://user:password@localhost/healthtwin

# CORS
ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# File Upload
MAX_FILE_SIZE=10485760
UPLOAD_DIR=/opt/healthtwin-ai/uploads

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/healthtwin/app.log
```

## Security Considerations

### SSL/TLS Configuration

1. **Use Let's Encrypt for free SSL certificates**
2. **Configure strong cipher suites**
3. **Enable HSTS headers**
4. **Implement proper CORS policies**

### Application Security

1. **Environment Variables**
   - Never commit secrets to version control
   - Use strong, unique SECRET_KEY
   - Rotate keys regularly

2. **Database Security**
   - Use strong passwords
   - Enable connection encryption
   - Regular backups with encryption

3. **File Upload Security**
   - Validate file types and sizes
   - Scan for malware
   - Store in secure location

4. **API Security**
   - Implement rate limiting
   - Use HTTPS only
   - Validate all inputs
   - Log security events

## Monitoring and Logging

### Application Monitoring

1. **Health Checks**
   - Endpoint: `/health`
   - Monitor database connectivity
   - Check disk space and memory

2. **Logging Configuration**
   ```python
   # In production settings
   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'handlers': {
           'file': {
               'level': 'INFO',
               'class': 'logging.FileHandler',
               'filename': '/var/log/healthtwin/app.log',
           },
       },
       'loggers': {
           'healthtwin': {
               'handlers': ['file'],
               'level': 'INFO',
               'propagate': True,
           },
       },
   }
   ```

3. **Metrics Collection**
   - Use Prometheus + Grafana
   - Monitor response times
   - Track error rates
   - Monitor resource usage

## Backup and Recovery

### Database Backup

```bash
# PostgreSQL
pg_dump -h localhost -U healthtwin_user healthtwin > backup_$(date +%Y%m%d).sql

# SQLite
cp healthtwin.db backup_healthtwin_$(date +%Y%m%d).db
```

### File Backup

```bash
# Backup uploads directory
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   sudo lsof -i :8000
   sudo kill -9 <PID>
   ```

2. **Permission Denied**
   ```bash
   sudo chown -R www-data:www-data /opt/healthtwin-ai
   sudo chmod -R 755 /opt/healthtwin-ai
   ```

3. **Database Connection Issues**
   - Check database service status
   - Verify connection credentials
   - Check firewall rules

4. **SSL Certificate Issues**
   ```bash
   sudo certbot renew --dry-run
   sudo systemctl restart nginx
   ```

For additional support, please refer to the [GitHub Issues](https://github.com/yourusername/Healthtwin-AI/issues) page.
