#!/bin/bash

# Setup script for FreeBitco.in Docker deployment
echo "🚀 Setting up FreeBitco.in Bot for Docker..."

# Create logs directory if it doesn't exist
if [ ! -d "logs" ]; then
    mkdir logs
    echo "✅ Created logs directory"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "⚠️  Created .env from .env.example - please edit with your values"
    else
        echo "❌ No .env or .env.example file found!"
        echo "Please create .env with:"
        echo "TELEGRAM_TOKEN=your_bot_token"
        echo "TELEGRAM_CHAT_ID=your_chat_id"
        echo "HEADLESS=false"
        echo "CHROME_PATH=/usr/bin/google-chrome"
        exit 1
    fi
fi

# Check if cookies.json exists
if [ ! -f "cookies.json" ]; then
    echo "⚠️  No cookies.json found!"
    echo "You need to generate cookies first. Options:"
    echo "1. Run locally: python getcookies.py"
    echo "2. Use Docker: docker-compose -f docker-compose.production.yml --profile cookie-gen up cookie-generator"
    echo "   Then connect to VNC at http://localhost:7901 and run: python3 getcookies.py"
fi

# Check required files
required_files=("app.py" "CloudflareBypasser.py" "requirements.txt")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "❌ Missing required files:"
    printf '%s\n' "${missing_files[@]}"
    exit 1
fi

echo "✅ All required files present"
echo ""
echo "🐳 Ready to start! Use one of these commands:"
echo ""
echo "# Start the bot:"
echo "docker-compose -f docker-compose.production.yml up -d"
echo ""
echo "# Generate cookies (if needed):"
echo "docker-compose -f docker-compose.production.yml --profile cookie-gen up cookie-generator"
echo ""
echo "# View logs:"
echo "docker-compose -f docker-compose.production.yml logs -f freebitcoin-bot"
echo ""
echo "# VNC access: http://localhost:7900 (password: freebitcoin123)"