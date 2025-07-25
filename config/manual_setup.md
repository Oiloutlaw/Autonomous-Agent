# Manual Setup Checklist

This file contains all manual configuration steps required before deploying the Autonomous-Agent system.

## ✅ Pre-Deployment Checklist

### 1. System Dependencies
- [ ] **Install Terraform** (required for infrastructure deployment)
  ```bash
  # Ubuntu/Debian
  sudo apt update && sudo apt install terraform
  
  # macOS
  brew install terraform
  
  # Verify installation
  terraform --version
  ```

- [ ] **Install Tor** (required for proxy rotation)
  ```bash
  # Ubuntu/Debian
  sudo apt install tor
  
  # macOS
  brew install tor
  
  # Configure Tor password in /etc/tor/torrc
  sudo nano /etc/tor/torrc
  # Add: HashedControlPassword [your-hashed-password]
  ```

### 2. API Key Acquisition

**Priority 1 - Critical (System will exit without these):**
- [ ] **OpenAI API Key** - Required for content generation
  - Sign up at: https://platform.openai.com/
  - Navigate to: API Keys section
  - Create new secret key
  - **Cost**: Pay-per-use, ~$0.002 per 1K tokens

**Priority 2 - Core Features:**
- [ ] **YouTube Data API Key** - Required for video uploads
  - Go to: https://console.cloud.google.com/
  - Enable: YouTube Data API v3
  - Create credentials: API Key
  - **Cost**: Free (10,000 units/day quota)

- [ ] **Stripe Secret Key** - Required for payment processing
  - Sign up at: https://dashboard.stripe.com/
  - Get from: Developers > API Keys
  - **Cost**: 2.9% + 30¢ per transaction

- [ ] **GitHub Token** - Required for repository operations
  - Go to: https://github.com/settings/tokens
  - Generate new token with `repo` and `workflow` scopes
  - **Cost**: Free

**Priority 3 - Enhanced Features:**
- [ ] **Reddit API Credentials** - For trend monitoring
  - Create app at: https://www.reddit.com/prefs/apps
  - Get: client_id, client_secret
  - **Cost**: Free

- [ ] **Email Service API** (choose one):
  - [ ] SendGrid: https://app.sendgrid.com/settings/api_keys
  - [ ] Mailchimp: https://admin.mailchimp.com/account/api/
  - **Cost**: Free tier available

**Priority 4 - Optional Analytics:**
- [ ] Google Ads API Key
- [ ] Google Analytics API Key  
- [ ] Ahrefs API Key
- [ ] WordPress API Key
- [ ] Bitly API Key

### 3. Infrastructure Setup

- [ ] **AWS Account Setup** (if using cloud deployment)
  ```bash
  # Install AWS CLI
  pip install awscli
  
  # Configure credentials
  aws configure
  # Enter: Access Key ID, Secret Access Key, Region (us-east-1)
  ```

- [ ] **Initialize Terraform**
  ```bash
  cd infra/
  terraform init
  terraform plan
  # Review the planned infrastructure
  terraform apply
  ```

### 4. Configuration Files

- [ ] **Copy API keys configuration**
  ```bash
  cp config/api_keys.yml.example config/api_keys.yml
  # Edit config/api_keys.yml with your actual API keys
  ```

- [ ] **Create environment file**
  ```bash
  cp .env.example .env
  # Edit .env with your configuration
  ```

- [ ] **Verify .gitignore protects secrets**
  ```bash
  # Ensure these files are in .gitignore:
  # .env
  # config/api_keys.yml
  # agent_memory.db
  # .terraform/
  ```

### 5. Testing & Validation

- [ ] **Test API connections**
  ```bash
  python -c "
  import openai
  import os
  from dotenv import load_dotenv
  load_dotenv()
  openai.api_key = os.getenv('OPENAI_API_KEY')
  print('✅ OpenAI connection test passed')
  "
  ```

- [ ] **Test infrastructure deployment**
  ```bash
  cd infra/
  terraform plan
  # Should show planned resources without errors
  ```

- [ ] **Test application startup**
  ```bash
  # Test each entry point
  python autonomous_agent.py --dry-run
  python SelfHealingLauncher.py --test
  python orchestrator.py --validate
  ```

### 6. Security Checklist

- [ ] **Verify secrets are not committed**
  ```bash
  git status
  # Should NOT show .env or api_keys.yml as staged
  ```

- [ ] **Set appropriate file permissions**
  ```bash
  chmod 600 .env config/api_keys.yml
  # Restrict access to owner only
  ```

- [ ] **Enable Tor for anonymous operations**
  ```bash
  sudo systemctl start tor
  sudo systemctl enable tor
  ```

## 🚨 Common Issues & Solutions

### Issue: "terraform: command not found"
**Solution**: Install Terraform using package manager or download from terraform.io

### Issue: "OpenAI API key invalid"
**Solution**: Verify key format starts with "sk-" and has sufficient credits

### Issue: "YouTube quota exceeded"
**Solution**: YouTube API has daily quotas. Wait 24 hours or request quota increase

### Issue: "Tor authentication failed"
**Solution**: Set TOR_PASSWORD in .env and configure HashedControlPassword in torrc

### Issue: "Infrastructure deployment fails"
**Solution**: Verify AWS credentials and permissions for S3, CloudWatch, IAM

## 📞 Support Resources

- **OpenAI API Docs**: https://platform.openai.com/docs
- **YouTube API Docs**: https://developers.google.com/youtube/v3
- **Terraform AWS Provider**: https://registry.terraform.io/providers/hashicorp/aws
- **CrewAI Documentation**: https://docs.crewai.com/
- **Stripe API Reference**: https://stripe.com/docs/api

## 🎯 Deployment Readiness Score

Complete this checklist to achieve 100% deployment readiness:

- [ ] All Priority 1 API keys configured (25%)
- [ ] System dependencies installed (25%) 
- [ ] Infrastructure deployed successfully (25%)
- [ ] Application startup tests pass (25%)

**Current Status**: ___% Ready for Production
