# 🚀 AWS Deployment Guide for Autonomous Agent

## 📋 Prerequisites
- AWS Account with EC2 access
- Basic familiarity with SSH and command line
- Domain name (optional but recommended)

## 🔧 Step 1: Download Code from GitHub

### Option A: Direct GitHub Download
1. Go to: https://github.com/Oiloutlaw/Autonomous-Agent
2. Click "Code" → "Download ZIP"
3. Extract the ZIP file to your local computer

### Option B: Git Clone (Recommended)
```bash
git clone https://github.com/Oiloutlaw/Autonomous-Agent.git
cd Autonomous-Agent
```

## ☁️ Step 2: Set Up AWS EC2 Instance

### Launch EC2 Instance
1. **Login to AWS Console** → EC2 Dashboard
2. **Launch Instance** with these settings:
   - **AMI**: Ubuntu Server 22.04 LTS
   - **Instance Type**: t3.medium (minimum) or t3.large (recommended)
   - **Storage**: 20GB GP3 SSD minimum
   - **Security Group**: Allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (App)

### Security Group Rules
```
Type        Protocol    Port Range    Source
SSH         TCP         22           Your IP/0.0.0.0/0
HTTP        TCP         80           0.0.0.0/0
HTTPS       TCP         443          0.0.0.0/0
Custom TCP  TCP         8000         0.0.0.0/0
```

## 🔑 Step 3: Connect to Your EC2 Instance

### SSH Connection
```bash
# Download your .pem key file from AWS
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

## 📦 Step 4: Install Dependencies on EC2

### System Updates & Python Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv git -y

# Install Docker (for containerized deployment)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
```

### Install Node.js (if needed)
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

## 📁 Step 5: Transfer Your Code to EC2

### Method A: Git Clone on EC2
```bash
# On your EC2 instance
git clone https://github.com/Oiloutlaw/Autonomous-Agent.git
cd Autonomous-Agent
```

### Method B: SCP File Transfer
```bash
# From your local computer
scp -i your-key.pem -r ./Autonomous-Agent ubuntu@your-ec2-ip:~/
```

### Method C: Upload via GitHub (Recommended)
```bash
# Push your local changes to GitHub first
git add .
git commit -m "Production deployment ready"
git push origin main

# Then clone on EC2
git clone https://github.com/Oiloutlaw/Autonomous-Agent.git
```

## 🔧 Step 6: Environment Setup on EC2

### Create Python Virtual Environment
```bash
cd Autonomous-Agent
python3 -m venv venv
source venv/bin/activate
```

### Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Create Production Environment File
```bash
# Create .env file with your API keys
nano .env
```

Add your production API keys:
```env
OPENAI_API_KEY=your-production-openai-key
YOUTUBE_API_KEY=your-youtube-api-key
STRIPE_SECRET_KEY=your-live-stripe-key
STRIPE_PUBLISHABLE_KEY=your-live-stripe-publishable-key
EMAIL=your-email@domain.com
EMAIL_PASSWORD=your-email-password
TOR_PASSWORD=your-tor-password
ENVIRONMENT=production
DOMAIN=your-domain.com
```

## 🚀 Step 7: Production Deployment Options

### Option A: Direct Python Execution
```bash
# Start the autonomous agent
python enhanced_launcher.py
```

### Option B: Docker Deployment (Recommended)
```bash
# Build Docker image
docker build -t autonomous-agent .

# Run container
docker run -d \
  --name autonomous-agent \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  autonomous-agent
```

### Option C: Systemd Service (Production)
```bash
# Create service file
sudo nano /etc/systemd/system/autonomous-agent.service
```

Service file content:
```ini
[Unit]
Description=Autonomous Agent
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Autonomous-Agent
Environment=PATH=/home/ubuntu/Autonomous-Agent/venv/bin
ExecStart=/home/ubuntu/Autonomous-Agent/venv/bin/python enhanced_launcher.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable autonomous-agent
sudo systemctl start autonomous-agent
sudo systemctl status autonomous-agent
```

## 🌐 Step 8: Domain & SSL Setup (Optional)

### Install Nginx
```bash
sudo apt install nginx -y
```

### Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/autonomous-agent
```

Nginx configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Enable SSL with Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

## 📊 Step 9: Monitoring & Maintenance

### Check System Status
```bash
# Check if service is running
sudo systemctl status autonomous-agent

# View logs
sudo journalctl -u autonomous-agent -f

# Check resource usage
htop
```

### Access Your Agent
- **Local**: http://your-ec2-ip:8000/metrics
- **With Domain**: https://your-domain.com/metrics

## 🔒 Step 10: Security Hardening

### Firewall Setup
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8000
```

### Regular Updates
```bash
# Create update script
nano update-agent.sh
```

Update script:
```bash
#!/bin/bash
cd /home/ubuntu/Autonomous-Agent
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart autonomous-agent
```

## 🎯 Quick Start Commands Summary

```bash
# 1. Launch EC2 instance (Ubuntu 22.04, t3.medium+)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. Install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git -y

# 4. Clone repository
git clone https://github.com/Oiloutlaw/Autonomous-Agent.git
cd Autonomous-Agent

# 5. Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. Configure environment
nano .env  # Add your API keys

# 7. Start agent
python enhanced_launcher.py
```

## 🚨 Troubleshooting

### Common Issues
1. **Port 8000 blocked**: Check security groups
2. **Python dependencies**: Ensure virtual environment is activated
3. **API key errors**: Verify .env file format
4. **Memory issues**: Upgrade to larger instance type

### Support Commands
```bash
# Check logs
tail -f /var/log/syslog | grep autonomous

# Monitor resources
free -h
df -h
```

Your autonomous agent will now run 24/7 on AWS, generating revenue automatically!
