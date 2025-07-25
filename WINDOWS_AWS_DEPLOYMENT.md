# 🪟 Windows AWS Deployment Guide for Autonomous Agent

## 🚨 **You're on Windows - Different Commands Needed!**

The previous guide had Linux commands. Here's the **Windows-specific** deployment process:

## 📋 **Prerequisites for Windows**
- Windows 10/11 with PowerShell
- AWS Account with EC2 access
- Git for Windows (download from git-scm.com)
- Optional: Windows Subsystem for Linux (WSL) for easier deployment

## 🔧 **Step 1: Download Code to Windows**

### Option A: Download ZIP from GitHub
1. **Go to:** https://github.com/Oiloutlaw/Autonomous-Agent
2. **Click:** "Code" → "Download ZIP"
3. **Extract:** Right-click ZIP → "Extract All" to `C:\Users\YourName\Autonomous-Agent`

### Option B: Git Clone (Recommended)
```powershell
# Open PowerShell as Administrator
cd C:\Users\$env:USERNAME
git clone https://github.com/Oiloutlaw/Autonomous-Agent.git
cd Autonomous-Agent
```

## ☁️ **Step 2: Set Up AWS EC2 Instance**

### Launch EC2 Instance (Same as Linux guide)
1. **AWS Console** → EC2 Dashboard → "Launch Instance"
2. **Settings:**
   - **AMI:** Ubuntu Server 22.04 LTS
   - **Instance Type:** t3.medium or larger
   - **Storage:** 20GB GP3 SSD minimum
   - **Key Pair:** Create new or use existing (.pem file)
   - **Security Group:** Allow ports 22, 80, 443, 8000

### Download Your Key File
1. **During EC2 setup:** Download the `.pem` key file
2. **Save to:** `C:\Users\YourName\Downloads\your-key-name.pem`
3. **Remember the exact filename!**

## 🔑 **Step 3: Connect from Windows**

### Method A: PowerShell with OpenSSH (Built into Windows 10/11)
```powershell
# Navigate to your key file location
cd C:\Users\$env:USERNAME\Downloads

# Set proper permissions (Windows equivalent of chmod 400)
icacls your-actual-key-name.pem /inheritance:r /grant:r "$env:USERNAME:(R)"

# Connect to EC2 (replace with YOUR actual IP and key name)
ssh -i your-actual-key-name.pem ubuntu@YOUR-ACTUAL-EC2-IP
```

### Method B: PuTTY (Alternative)
1. **Download PuTTY:** https://www.putty.org/
2. **Convert .pem to .ppk:** Use PuTTYgen to convert your .pem file
3. **Connect:** Use PuTTY with your .ppk key and EC2 IP

### Method C: Windows Subsystem for Linux (WSL)
```powershell
# Install WSL if not already installed
wsl --install

# Then use Linux commands in WSL
wsl
chmod 400 /mnt/c/Users/YourName/Downloads/your-key.pem
ssh -i /mnt/c/Users/YourName/Downloads/your-key.pem ubuntu@your-ec2-ip
```

## 📦 **Step 4: Setup on EC2 (Once Connected)**

```bash
# These commands run on your EC2 instance (Linux)
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git -y

# Clone your repository
git clone https://github.com/Oiloutlaw/Autonomous-Agent.git
cd Autonomous-Agent

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 🔧 **Step 5: Transfer Files from Windows (If Needed)**

### Method A: SCP from PowerShell
```powershell
# From your Windows PowerShell (in the Autonomous-Agent folder)
scp -i C:\Users\YourName\Downloads\your-key.pem -r . ubuntu@YOUR-EC2-IP:~/Autonomous-Agent-Windows/
```

### Method B: WinSCP (GUI Tool)
1. **Download WinSCP:** https://winscp.net/
2. **Connect:** Use your .pem key and EC2 IP
3. **Drag & Drop:** Transfer files via GUI

### Method C: Git Push/Pull (Recommended)
```powershell
# On Windows - push your changes to GitHub
git add .
git commit -m "Windows deployment ready"
git push origin main

# On EC2 - pull the changes
git pull origin main
```

## 🔒 **Step 6: Configure Environment on EC2**

```bash
# On your EC2 instance, create .env file
nano .env
```

**Add your API keys (NEVER commit this file):**
```env
OPENAI_API_KEY=your-production-openai-key
YOUTUBE_API_KEY=your-youtube-api-key
STRIPE_SECRET_KEY=your-live-stripe-key
STRIPE_PUBLISHABLE_KEY=your-live-stripe-publishable-key
EMAIL=your-email@domain.com
EMAIL_PASSWORD=your-email-password
ENVIRONMENT=production
```

## 🚀 **Step 7: Start Your Agent**

```bash
# Test run
python enhanced_launcher.py

# Production service (recommended)
sudo nano /etc/systemd/system/autonomous-agent.service
```

**Service file content:**
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

**Enable service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable autonomous-agent
sudo systemctl start autonomous-agent
sudo systemctl status autonomous-agent
```

## 🌐 **Step 8: Access Your Agent**

**Your agent will be available at:**
- `http://YOUR-EC2-IP:8000/metrics`
- `http://YOUR-EC2-IP:8000/status`

## 🔧 **Windows-Specific Troubleshooting**

### Common Windows Issues:

**1. "ssh: command not found"**
```powershell
# Enable OpenSSH Client (Windows 10/11)
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

**2. Permission denied (publickey)**
```powershell
# Check key permissions
icacls your-key.pem
# Should show only your username with Read permissions
```

**3. "Could not resolve hostname"**
- Replace `your-ec2-public-ip` with your ACTUAL EC2 public IP
- Find it in AWS Console → EC2 → Instances → Your Instance

**4. PowerShell execution policy**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 🎯 **Quick Windows Deployment Checklist**

```powershell
# 1. Download code
git clone https://github.com/Oiloutlaw/Autonomous-Agent.git

# 2. Get EC2 IP from AWS Console (e.g., 54.123.45.67)

# 3. Set key permissions
icacls your-key.pem /inheritance:r /grant:r "$env:USERNAME:(R)"

# 4. Connect to EC2
ssh -i your-key.pem ubuntu@54.123.45.67

# 5. On EC2: Setup environment
sudo apt update && sudo apt install python3 python3-pip python3-venv git -y
git clone https://github.com/Oiloutlaw/Autonomous-Agent.git
cd Autonomous-Agent
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 6. Create .env with your API keys
nano .env

# 7. Start agent
python enhanced_launcher.py
```

## 📱 **Alternative: Use AWS CloudShell**

**Easiest option for Windows users:**
1. **AWS Console** → Search "CloudShell"
2. **Click** CloudShell icon (terminal in browser)
3. **Run deployment commands** directly in browser
4. **No SSH setup needed!**

```bash
# In AWS CloudShell
git clone https://github.com/Oiloutlaw/Autonomous-Agent.git
cd Autonomous-Agent
# Follow Linux deployment steps
```

## 🎉 **Success!**

Once deployed, your autonomous agent will run 24/7 on AWS, generating revenue automatically toward your $50k/month goal!

**Access your live agent:**
- **Metrics:** `http://YOUR-EC2-IP:8000/metrics`
- **Status:** `http://YOUR-EC2-IP:8000/status`

Remember to replace ALL placeholder values with your actual:
- Key file name
- EC2 public IP address
- API keys in .env file
