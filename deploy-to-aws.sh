#!/bin/bash


set -e

EC2_IP=$1
KEY_FILE=$2

if [ -z "$EC2_IP" ] || [ -z "$KEY_FILE" ]; then
    echo "Usage: $0 <ec2-ip> <key-file>"
    echo "Example: $0 54.123.45.67 my-key.pem"
    exit 1
fi

echo "🚀 Deploying Autonomous Agent to AWS EC2: $EC2_IP"

echo "📦 Creating deployment package..."
tar -czf autonomous-agent-deploy.tar.gz \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.db' \
    --exclude='.env' \
    --exclude='venv' \
    .

echo "📁 Transferring files to EC2..."
scp -i "$KEY_FILE" autonomous-agent-deploy.tar.gz ubuntu@$EC2_IP:~/
scp -i "$KEY_FILE" AWS_DEPLOYMENT_GUIDE.md ubuntu@$EC2_IP:~/

echo "🔧 Setting up environment on EC2..."
ssh -i "$KEY_FILE" ubuntu@$EC2_IP << 'EOF'
    tar -xzf autonomous-agent-deploy.tar.gz
    cd Autonomous-Agent || mkdir Autonomous-Agent && cd Autonomous-Agent
    
    sudo apt update && sudo apt upgrade -y
    
    sudo apt install python3 python3-pip python3-venv git htop -y
    
    python3 -m venv venv
    source venv/bin/activate
    
    pip install -r requirements.txt
    
    echo "✅ Environment setup complete!"
    echo "📝 Next steps:"
    echo "1. Create .env file with your API keys"
    echo "2. Run: source venv/bin/activate"
    echo "3. Run: python enhanced_launcher.py"
    echo ""
    echo "📖 See AWS_DEPLOYMENT_GUIDE.md for detailed instructions"
EOF

rm autonomous-agent-deploy.tar.gz

echo "🎉 Deployment complete!"
echo "🔗 SSH to your instance: ssh -i $KEY_FILE ubuntu@$EC2_IP"
echo "📊 Once running, access your agent at: http://$EC2_IP:8000/metrics"
