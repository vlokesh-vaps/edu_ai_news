# Deployment Guide for edu-news-ticker

This guide provides instructions for deploying the edu-news-ticker application to various platforms.

## Pre-Deployment Checklist

- [ ] All code is tested and working locally
- [ ] `.env` file is configured with production Groq API key
- [ ] `.env` file is in `.gitignore` (already done)
- [ ] `requirements.txt` is up to date
- [ ] All documentation is complete
- [ ] No sensitive information is committed to git

## Local Deployment (Development)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your Groq API key
echo GROQ_API_KEY=your_key_here > .env

# Run the application
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## Docker Deployment

### Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build and Run Docker Image

```bash
# Build image
docker build -t edu-news-ticker:latest .

# Run container
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your_key_here \
  edu-news-ticker:latest
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

Run with:
```bash
docker-compose up
```

## Vercel Deployment

The project includes `vercel.json` configuration.

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/your-username/edu-news-ticker.git
git push -u origin main
```

### Step 2: Connect to Vercel

1. Go to https://vercel.com
2. Click "New Project"
3. Import your GitHub repository
4. Configure environment variables:
   - `GROQ_API_KEY`: Your Groq API key
   - `LOG_LEVEL`: INFO
5. Deploy

## Heroku Deployment

### Prerequisites

- Heroku CLI installed
- Heroku account

### Deployment Steps

```bash
# Login to Heroku
heroku login

# Create app
heroku create edu-news-ticker

# Add environment variables
heroku config:set GROQ_API_KEY=your_key_here
heroku config:set LOG_LEVEL=INFO

# Create Procfile in project root
echo "web: uvicorn app.main:app --host 0.0.0.0 --port 8000" > Procfile

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

## AWS EC2 Deployment

### Step 1: Launch EC2 Instance

- Ubuntu 22.04 LTS
- t2.micro (free tier eligible)
- Open ports 80, 443, 8000

### Step 2: Install Dependencies

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python and pip
sudo apt install python3-pip python3-venv -y

# Install git
sudo apt install git -y
```

### Step 3: Clone and Setup Application

```bash
# Clone repository
git clone https://github.com/your-username/edu-news-ticker.git
cd edu-news-ticker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GROQ_API_KEY=your_key_here" > .env
```

### Step 4: Run with Gunicorn

```bash
# Install Gunicorn
pip install gunicorn

# Run application
gunicorn -w 4 -b 0.0.0.0:8000 app.main:app
```

### Step 5: Setup Systemd Service

Create `/etc/systemd/system/edu-news-ticker.service`:

```ini
[Unit]
Description=edu-news-ticker API
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/edu-news-ticker
Environment="PATH=/home/ubuntu/edu-news-ticker/venv/bin"
EnvironmentFile=/home/ubuntu/edu-news-ticker/.env
ExecStart=/home/ubuntu/edu-news-ticker/venv/bin/gunicorn -w 4 -b 0.0.0.0:8000 app.main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable edu-news-ticker
sudo systemctl start edu-news-ticker
sudo systemctl status edu-news-ticker
```

### Step 6: Setup Nginx Reverse Proxy

Install Nginx:
```bash
sudo apt install nginx -y
```

Configure `/etc/nginx/sites-available/edu-news-ticker`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/edu-news-ticker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 7: Setup SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

## Google Cloud Run Deployment

### Prerequisites

- Google Cloud account
- gcloud CLI installed

### Deployment Steps

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Build and push to Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/edu-news-ticker

# Deploy to Cloud Run
gcloud run deploy edu-news-ticker \
  --image gcr.io/YOUR_PROJECT_ID/edu-news-ticker \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GROQ_API_KEY=your_key_here
```

## DigitalOcean App Platform

### Step 1: Create App Spec

Create `app.yaml`:

```yaml
name: edu-news-ticker
services:
- name: api
  github:
    branch: main
    repo: your-username/edu-news-ticker
  build_command: pip install -r requirements.txt
  run_command: uvicorn app.main:app --host 0.0.0.0 --port 8080
  http_port: 8080
  envs:
  - key: GROQ_API_KEY
    value: ${GROQ_API_KEY}
  - key: LOG_LEVEL
    value: INFO
```

### Step 2: Deploy

```bash
# Install doctl
# https://docs.digitalocean.com/reference/doctl/how-to/install/

# Create app
doctl apps create --spec app.yaml
```

## Production Best Practices

### Environment Variables

```env
# Production
GROQ_API_KEY=your_production_key
LOG_LEVEL=INFO
```

### Security

1. **API Key Management**
   - Use secrets management service
   - Rotate keys regularly
   - Monitor API usage

2. **CORS Configuration**
   ```python
   # In app/main.py, update CORS settings
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-frontend-domain.com"],  # Specific domain
       allow_credentials=True,
       allow_methods=["GET"],
       allow_headers=["*"],
   )
   ```

3. **Rate Limiting**
   Install slowapi:
   ```bash
   pip install slowapi
   ```
   
   Add to app/main.py:
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   
   @app.get("/api/news")
   @limiter.limit("30/minute")
   async def get_news(request: Request, limit: int = 10):
       ...
   ```

4. **HTTPS**
   - Always use HTTPS in production
   - Use Let's Encrypt for free SSL certificates
   - Enforce HTTPS redirects

5. **Monitoring & Logging**
   - Use centralized logging (e.g., DataDog, Loggly)
   - Setup alerts for errors
   - Monitor API response times

### Performance

1. **Caching**
   - Add Redis for caching feed results
   - Cache headlines for 1 hour
   - Reduce API calls

2. **Async Processing**
   - Convert RSS fetching to async
   - Process multiple feeds in parallel
   - Reduce latency

3. **Database**
   - Consider storing headlines in database
   - Enable full-text search
   - Archive old headlines

## Monitoring

### Health Checks

Setup health check endpoints for monitoring:

```bash
# Kubernetes health checks
liveness: GET /
readiness: GET /api
```

### Logging

Monitor application logs:

```bash
# Docker
docker logs -f container_name

# Heroku
heroku logs --tail

# EC2 with systemd
sudo journalctl -u edu-news-ticker -f
```

### Alerting

Setup alerts for:
- High error rate (>5%)
- API response time >5s
- Feed fetch failures
- API quota exhaustion

## Troubleshooting Production Issues

### 500 Errors
1. Check logs for detailed error messages
2. Verify Groq API key is valid
3. Check feed URLs are accessible

### Slow Response Times
1. Check network latency
2. Profile RSS feed fetching
3. Consider adding caching

### High Memory Usage
1. Monitor headline count
2. Implement pagination
3. Add memory limits

### Feed Failures
1. Check feed URLs
2. Verify network connectivity
3. Monitor RSS feed availability

## Rollback Plan

```bash
# Docker
docker run -d -p 8000:8000 \
  -e GROQ_API_KEY=key \
  edu-news-ticker:previous_tag

# Heroku
heroku releases:rollback

# Git (if needed)
git revert HEAD
git push production main
```

## Support & Maintenance

- **Update dependencies regularly**: `pip install --upgrade -r requirements.txt`
- **Monitor Groq API pricing and usage**
- **Archive old headlines periodically**
- **Review and optimize feed list**
- **Update security patches**

---

For more information, see `README.md` and `SETUP_GUIDE.md`.

