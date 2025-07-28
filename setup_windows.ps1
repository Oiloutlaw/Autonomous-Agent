# Windows Setup Script for Autonomous Agent
# Run this script as Administrator in PowerShell

Write-Host "🚀 Setting up Autonomous Agent for Windows..." -ForegroundColor Green

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Install Chocolatey if not present
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "📦 Installing Chocolatey package manager..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
}

# Install Python if not present
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "🐍 Installing Python..." -ForegroundColor Yellow
    choco install python3 -y
    refreshenv
}

# Install FFmpeg
Write-Host "🎬 Installing FFmpeg..." -ForegroundColor Yellow
choco install ffmpeg -y

# Install Git if not present
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "📚 Installing Git..." -ForegroundColor Yellow
    choco install git -y
}

# Install Terraform
Write-Host "🏗️ Installing Terraform..." -ForegroundColor Yellow
choco install terraform -y

# Install Tor Browser (optional)
Write-Host "🔒 Installing Tor Browser (optional for proxy features)..." -ForegroundColor Yellow
choco install tor-browser -y

# Refresh environment variables
refreshenv

# Install Python dependencies
if (Test-Path "requirements.txt") {
    Write-Host "📋 Installing Python dependencies..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    
    # Install Playwright browsers
    Write-Host "🌐 Installing Playwright browsers..." -ForegroundColor Yellow
    python -m playwright install
} else {
    Write-Host "⚠️ requirements.txt not found. Make sure you're in the project directory." -ForegroundColor Yellow
}

# Create necessary directories
Write-Host "📁 Creating directories..." -ForegroundColor Yellow
if (!(Test-Path "output")) { New-Item -ItemType Directory -Path "output" }
if (!(Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" }

# Create secrets directory in AppData
$secretsDir = "$env:APPDATA\autonomous-agent\secrets"
if (!(Test-Path $secretsDir)) {
    New-Item -ItemType Directory -Path $secretsDir -Force
    Write-Host "🔐 Created secrets directory: $secretsDir" -ForegroundColor Green
}

Write-Host "✅ Windows setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Copy your .env file with API keys to this directory" -ForegroundColor White
Write-Host "2. Or place API key files in: $secretsDir" -ForegroundColor White
Write-Host "3. Run: python autonomous_agent.py" -ForegroundColor White
Write-Host ""
Write-Host "For Tor proxy features, configure Tor Browser control port in torrc file" -ForegroundColor Yellow
