# Unraid Quick Start Guide

## Prerequisites

- Your existing working files: `app.py`, `CloudflareBypasser.py`, `requirements.txt`
- Generated `cookies.json` file
- Configured `.env` file

## Setup Steps

### 1. Copy Files to Unraid

```bash
# Create directory on Unraid
mkdir -p /mnt/user/appdata/freebitcoin-bot
cd /mnt/user/appdata/freebitcoin-bot

# Copy your working files:
# - app.py
# - CloudflareBypasser.py
# - requirements.txt
# - .env
# - cookies.json
# - docker-compose.production.yml
```

### 2. Verify Your .env File

```env
TELEGRAM_TOKEN=your_actual_bot_token
TELEGRAM_CHAT_ID=your_actual_chat_id
HEADLESS=false
CHROME_PATH=/usr/bin/google-chrome
```

### 3. Start the Bot

```bash
# From your project directory
docker-compose -f docker-compose.production.yml up -d
```

### 4. Monitor the Bot

```bash
# View logs
docker-compose -f docker-compose.production.yml logs -f freebitcoin-bot

# VNC access (if needed)
# http://your-unraid-ip:7900 (password: freebitcoin123)
```

## If You Need to Generate Cookies in Docker

### Option 1: Generate Locally First (Recommended)

```bash
# On your Windows machine
python getcookies.py
# Then copy cookies.json to Unraid
```

### Option 2: Generate in Docker

```bash
# Start cookie generator
docker-compose -f docker-compose.production.yml --profile cookie-gen up cookie-generator

# Connect to VNC at http://your-unraid-ip:7901 (password: cookies123)
# In VNC terminal: python3 getcookies.py
# Follow prompts to login and save cookies
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.production.yml logs freebitcoin-bot

# Common issues:
# - Missing .env file
# - Missing cookies.json
# - Incorrect file permissions
```

### Bot Stuck on Cloudflare

```bash
# Connect via VNC to manually solve captcha
# http://your-unraid-ip:7900 (password: freebitcoin123)
```

### Update Bot

```bash
# Stop container
docker-compose -f docker-compose.production.yml down

# Update your files (app.py, etc.)

# Restart
docker-compose -f docker-compose.production.yml up -d
```

## File Structure on Unraid

```
/mnt/user/appdata/freebitcoin-bot/
├── app.py                           # Your working script
├── CloudflareBypasser.py           # Cloudflare bypass module
├── requirements.txt                # Python dependencies
├── .env                           # Your environment variables
├── cookies.json                   # Authentication cookies
├── docker-compose.production.yml  # Docker configuration
├── logs/                          # Log files (auto-created)
└── cloudflare_bypass.log         # Main log file
```

This setup uses your existing `app.py` without any modifications - it should work exactly like it does on your Windows machine!
