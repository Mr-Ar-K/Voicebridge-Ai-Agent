# VoiceBridge Backend - Deployment Guide

## Production Deployment Strategy

This guide covers deploying VoiceBridge backend to production environments.

## Pre-Deployment Checklist

- [ ] All API keys obtained and stored securely
- [ ] Qdrant instance provisioned (cloud or self-hosted)
- [ ] SSL certificates configured
- [ ] Environment variables configured
- [ ] Database seeded with schemes
- [ ] API rate limiting configured
- [ ] Monitoring and logging setup
- [ ] Backup strategy defined

## Deployment Options

### Option 1: Local Development Setup (No Docker)

#### 1. Install Qdrant Locally
```bash
# Linux/macOS
curl -L https://github.com/qdrant/qdrant/releases/download/v2.7.0/qdrant-x86_64-unknown-linux-gnu -o qdrant
chmod +x qdrant

# Or on macOS with Homebrew (if available)
brew install qdrant
```

#### 2. Deploy Backend
```bash
# Clone repository
git clone <your-repo-url>
cd Voicebridge-Ai-Agent/backend

# Create environment file
cp .env.example .env
# Edit .env with your credentials

# Setup Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# In one terminal - start Qdrant
./qdrant

# In another terminal - upload data
python upload_data.py

# In another terminal - run backend
python main.py
```

### Option 2: AWS EC2 + Docker

#### 1. Setup EC2 Instance
```bash
# Launch Ubuntu 20.04/22.04 instance
# Security group: Allow ports 80, 443, 6333

# SSH into instance
ssh -i key.pem ubuntu@your-instance-ip

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
```

#### 2. Deploy Backend
```bash
# Clone repository
git clone <your-repo-url>
cd Voicebridge-Ai-Agent/backend

# Create environment file
cat > .env << EOF
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_key
EOF

# Build and run with Docker Compose
docker-compose up -d
```

### Option 2: Google Cloud Run

#### 1. Setup Google Cloud
```bash
# Install gcloud CLI
# Initialize project
gcloud init

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable iam.googleapis.com
```

#### 2. Deploy
```bash
# Build container
docker build -t voicebridge-backend .

# Tag for GCR
docker tag voicebridge-backend gcr.io/YOUR_PROJECT_ID/voicebridge-backend

# Push to GCR
docker push gcr.io/YOUR_PROJECT_ID/voicebridge-backend

# Deploy to Cloud Run
gcloud run deploy voicebridge-backend \
  --image gcr.io/YOUR_PROJECT_ID/voicebridge-backend \
  --platform managed \
  --region us-central1 \
  --set-env-vars GEMINI_API_KEY=your_key,OPENAI_API_KEY=your_key
```

### Option 3: Heroku

#### 1. Setup Heroku
```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create new app
heroku create voicebridge-backend
```

#### 2. Configure and Deploy
```bash
# Set environment variables
heroku config:set GEMINI_API_KEY=your_key
heroku config:set OPENAI_API_KEY=your_key

# Deploy
git push heroku main
```

### Option 4: Kubernetes

#### 1. Create Deployment Manifest

**k8s/deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: voicebridge-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: voicebridge-backend
  template:
    metadata:
      labels:
        app: voicebridge-backend
    spec:
      containers:
      - name: backend
        image: voicebridge-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: voicebridge-secrets
              key: gemini-api-key
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: voicebridge-secrets
              key: openai-api-key
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1"
            memory: "1Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: voicebridge-backend-service
spec:
  selector:
    app: voicebridge-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### 2. Deploy
```bash
# Create secrets
kubectl create secret generic voicebridge-secrets \
  --from-literal=gemini-api-key=your_key \
  --from-literal=openai-api-key=your_key

# Deploy
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get pods
kubectl get svc
```

## Production Configuration

### Environment Variables
```bash
# Essential
export GEMINI_API_KEY="production_key"
export OPENAI_API_KEY="production_key"

# Qdrant
export QDRANT_URL="https://your-qdrant-instance.com"
export QDRANT_API_KEY="production_key"

# App Config
export ENVIRONMENT="production"
export LOG_LEVEL="INFO"
```

### Nginx Reverse Proxy Configuration

**nginx.conf**
```nginx
upstream backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Cache static docs
    location ~ ^/(docs|redoc|openapi.json)$ {
        proxy_pass http://backend;
        expires 1h;
        add_header Cache-Control "public, max-age=3600";
    }
}
```

### Systemd Service (Ubuntu/Debian)

**/etc/systemd/system/voicebridge.service**
```ini
[Unit]
Description=VoiceBridge Backend
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/home/www-data/voicebridge
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable voicebridge.service
sudo systemctl start voicebridge.service
sudo systemctl status voicebridge.service
```

## Monitoring & Logging

### Using PM2 (Process Manager)

```bash
npm install -g pm2

# Create ecosystem.config.js
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'voicebridge-backend',
    script: 'python',
    args: '-m uvicorn main:app --host 0.0.0.0 --port 8000',
    env: {
      PYTHONUNBUFFERED: 1,
      NODE_ENV: 'production'
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    watch: false,
    instances: 'max',
    exec_mode: 'cluster'
  }]
};
EOF

# Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### Logging with ELK Stack

**Using Docker Compose:**
```yaml
elasticsearch:
  image: elasticsearch:8.0.0
  ports:
    - "9200:9200"

kibana:
  image: kibana:8.0.0
  ports:
    - "5601:5601"

logstash:
  image: logstash:8.0.0
  volumes:
    - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
```

### Monitoring with Prometheus

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'voicebridge-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

## Database Management

### Qdrant Cloud Setup

1. Create account at https://cloud.qdrant.io
2. Create cluster
3. Get URL and API key
4. Update environment variables

### Backup Strategy

```bash
# Backup Qdrant collection
curl -X POST https://your-qdrant-instance/collections/government_schemes/snapshots

# Restore from snapshot
curl -X POST https://your-qdrant-instance/collections/government_schemes/snapshots/snapshot_name/recover
```

## Security Hardening

### Before Going Live

1. **Network Security**
   - Enable firewall
   - Restrict ports (only 80, 443)
   - Use VPC/security groups

2. **API Security**
   - Enable authentication (API keys)
   - Implement rate limiting
   - Add request signing

3. **Data Security**
   - Enable encryption at rest
   - Enable encryption in transit (HTTPS)
   - Regular security audits

4. **Application Security**
   - Update dependencies regularly
   - Run security scanners
   - Implement CORS properly

```python
# Example CORS configuration for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Performance Tuning

### Production FastAPI Settings

```bash
# Run with multiple workers
uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --max-requests 1000 \
  --max-requests-jitter 100
```

### Gunicorn + Uvicorn

```bash
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

## Continuous Deployment

### GitHub Actions Workflow

**.github/workflows/deploy.yml**
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Build Docker image
      run: docker build -t voicebridge-backend .
    
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USER }} --password-stdin
        docker tag voicebridge-backend:latest ${{ secrets.DOCKER_USER }}/voicebridge-backend:latest
        docker push ${{ secrets.DOCKER_USER }}/voicebridge-backend:latest
    
    - name: Deploy to production
      run: |
        # Deploy commands here
```

## Troubleshooting

### Service won't start
```bash
# Check logs
docker logs voicebridge-backend
journalctl -u voicebridge.service -f

# Check port conflicts
lsof -i :8000
```

### API key errors
```bash
# Verify keys are set
echo $GEMINI_API_KEY
echo $OPENAI_API_KEY

# Update .env
source .env
```

### High memory usage
```bash
# Check process memory
ps aux | grep python

# Limit container memory
docker run -m 512m voicebridge-backend
```

## Rollback Procedure

```bash
# Docker Compose rollback
docker-compose down
git checkout previous-version-tag
docker-compose up -d

# Kubernetes rollback
kubectl rollout history deployment/voicebridge-backend
kubectl rollout undo deployment/voicebridge-backend --to-revision=1
```

---

**Document Version:** 1.0
**Last Updated:** 2024
**For updates:** Check deployment documentation regularly
