# Windows Setup Guide for Autonomous Agent

This guide provides comprehensive instructions for setting up the Autonomous Agent system on Windows.

## Quick Start (Recommended)

### Option 1: Automated PowerShell Setup
1. Open PowerShell as Administrator
2. Run the automated setup script:
   ```powershell
   .\setup_windows.ps1
   ```

### Option 2: Manual Installation

#### Prerequisites
- Windows 10/11 or Windows Server 2019+
- PowerShell 5.1 or later
- Administrator privileges for initial setup

#### Step 1: Install Package Manager
Install Chocolatey for easy dependency management:
```powershell
# Run as Administrator
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

#### Step 2: Install System Dependencies

**Python** (if not already installed):
```powershell
# Via Chocolatey
choco install python3 -y

# Or via Winget
winget install Python.Python.3

# Verify installation
python --version
```

**FFmpeg** (required for video processing):
```powershell
# Via Chocolatey (recommended)
choco install ffmpeg -y

# Or via Winget
winget install FFmpeg

# Or download manually from: https://ffmpeg.org/download.html#build-windows
# Add to PATH environment variable
```

**Terraform** (required for infrastructure):
```powershell
# Via Chocolatey
choco install terraform -y

# Or via Winget
winget install HashiCorp.Terraform

# Verify installation
terraform --version
```

**Git** (if not already installed):
```powershell
choco install git -y
```

**Tor Browser** (optional, for proxy features):
```powershell
# Via Chocolatey
choco install tor-browser -y

# Or download from: https://www.torproject.org/download/
```

#### Step 3: Clone and Setup Project
```powershell
# Clone the repository
git clone https://github.com/Oiloutlaw/Autonomous-Agent.git
cd Autonomous-Agent

# Install Python dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install
```

#### Step 4: Configure API Keys
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_openai_key_here
GITHUB_TOKEN=your_github_token_here
STRIPE_SECRET_KEY=your_stripe_key_here
YOUTUBE_API_KEY=your_youtube_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
MODELSLAB_API_KEY=your_modelslab_key_here
TOR_PASSWORD=your_tor_password_here
```

Alternatively, store API keys in: `%APPDATA%\autonomous-agent\secrets\`

#### Step 5: Test Installation
```powershell
# Test platform utilities
python test_platform_utils.py

# Test basic functionality (dry run)
python autonomous_agent.py --help
```

## Docker Setup (Windows)

### Option 1: Windows Containers
```powershell
# Build Windows container
docker build -f Dockerfile.windows -t autonomous-agent-windows .

# Run container
docker run -p 8000:8000 autonomous-agent-windows

# Or use docker-compose
docker-compose --profile windows up --build
```

### Option 2: WSL + Linux Containers (Recommended)
1. Install WSL2:
   ```powershell
   wsl --install
   ```
2. Install Ubuntu from Microsoft Store
3. Use standard Linux Docker setup within WSL

## Tor Configuration (Optional)

For proxy rotation features, configure Tor:

1. Install Tor Browser or Tor service
2. Configure control port in torrc file (usually in `%APPDATA%\tor\torrc`):
   ```
   ControlPort 9051
   HashedControlPassword [your_hashed_password]
   ```
3. Set TOR_PASSWORD in your .env file

## Troubleshooting

### Common Issues

**FFmpeg not found:**
- Ensure FFmpeg is installed and in PATH
- Restart PowerShell after installation
- Test with: `ffmpeg -version`

**Terraform not found:**
- Verify installation: `terraform --version`
- Check PATH environment variable
- Reinstall via Chocolatey if needed

**Python import errors:**
- Ensure you're in the project directory
- Verify virtual environment is activated (if using one)
- Check that utils/platform_utils.py exists

**PowerShell execution policy:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Path-related errors:**
- The system now uses cross-platform path handling
- Ensure you're using the latest version with Windows compatibility fixes

### Performance Tips

1. **Use SSD storage** for better I/O performance
2. **Increase virtual memory** if processing large videos
3. **Use WSL2** for better Linux compatibility if needed
4. **Configure Windows Defender exclusions** for the project directory

## Windows-Specific Features

The system now includes:
- ✅ Cross-platform path normalization
- ✅ Windows-compatible shell commands
- ✅ FFmpeg Windows detection and installation guidance
- ✅ Terraform Windows support
- ✅ Tor Windows configuration
- ✅ PowerShell-compatible setup scripts
- ✅ Windows container support
- ✅ Graceful fallbacks for missing dependencies

## Support

For Windows-specific issues:
1. Check this guide first
2. Run the automated setup script
3. Verify all dependencies are installed
4. Check GitHub Issues for known problems
5. Consider using WSL2 for a Linux-like environment

The system maintains full backward compatibility with Linux/Unix while providing native Windows support.
