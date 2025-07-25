FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system and Node.js dependencies
RUN apt-get update && apt-get install -y \
    curl unzip git libssl-dev libffi-dev build-essential wget gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g playwright

# Copy app files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps

# Run the agent
CMD ["python", "autonomous_agent.py"]
