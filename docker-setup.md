# Docker Setup for FreeBitco.in Bot

## Problem: Cloudflare Captcha Loop in Docker

When running in Docker containers, Cloudflare often detects automation and presents unsolvable captchas, creating an infinite loop.

## Solution 1: Manual Cookie Generation + Docker Automation

### Step 1: Generate Cookies on Host Machine

```bash
# On your Unraid host or any machine with GUI
python getcookies.py
```

### Step 2: Copy cookies.json to Docker Container

```bash
# Copy the generated cookies to your Docker volume
cp cookies.json /path/to/docker/volume/cookies.json
```

### Step 3: Modified Docker Compose

```yaml
services:
  freebitcoin-bot:
    image: selenium/standalone-chrome:131.0-20241225
    container_name: freebitcoin-bot
    ports:
      - "4444:4444"
      - "7900:7900"
    volumes:
      - ./app:/app
      - ./cookies.json:/app/cookies.json # Mount cookies
      - ./logs:/app/logs
    environment:
      - TELEGRAM_TOKEN=your_token
      - TELEGRAM_CHAT_ID=your_chat_id
      - HEADLESS=true
      - SE_VNC_PASSWORD=password
    working_dir: /app
    command: python app.py
```

## Solution 2: Hybrid Approach - Manual Captcha Solving

Modify the script to pause and wait for manual intervention when Cloudflare is detected.
