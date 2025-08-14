# Unraid Docker Setup Guide for FreeBitco.in Bot

## The Problem

Cloudflare detects automated browsers in Docker containers and presents captchas that can't be solved programmatically, creating infinite loops.

## The Solution

Use a hybrid approach: automated execution with manual captcha intervention via VNC.

## Setup Steps

### 1. Prepare Your Files on Unraid

Create a directory on your Unraid server:

```bash
mkdir -p /mnt/user/appdata/freebitcoin-bot
cd /mnt/user/appdata/freebitcoin-bot
```

Copy these files to the directory:

- `app_docker.py` (the Docker-optimized version)
- `CloudflareBypasser.py`
- `requirements.txt`
- `docker-compose.unraid.yml`
- `.env` (create from `.env.example`)

### 2. Create Environment File

Create `.env` file:

```bash
TELEGRAM_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
HEADLESS=false
CHROME_PATH=/usr/bin/google-chrome
```

### 3. Generate Cookies (One-time Setup)

Option A - Generate cookies on host machine:

```bash
# On a machine with GUI
python getcookies.py
# Copy the generated cookies.json to your Unraid directory
```

Option B - Generate cookies in Docker:

```bash
# Start cookie generator container
docker-compose -f docker-compose.unraid.yml --profile cookie-gen up cookie-generator

# Connect to VNC at http://your-unraid-ip:7901 (password: cookies123)
# In VNC terminal, run: python3 getcookies.py
# Follow the prompts to login and save cookies
# Stop the container when done
```

### 4. Start the Bot

```bash
docker-compose -f docker-compose.unraid.yml up -d freebitcoin-bot
```

### 5. Monitor and Intervene When Needed

- **View logs**: `docker-compose -f docker-compose.unraid.yml logs -f freebitcoin-bot`
- **VNC access**: http://your-unraid-ip:7900 (password: freebitcoin123)
- **When Cloudflare appears**: Connect via VNC and solve the captcha manually

## How It Works

1. **Automated Operation**: The bot runs normally, using cookies for authentication
2. **Cloudflare Detection**: When Cloudflare is detected, the bot pauses and waits
3. **Manual Intervention**: You connect via VNC and solve the captcha
4. **Resume Automation**: Once solved, the bot continues automatically
5. **Telegram Notifications**: You get notified of successful rolls and balance updates

## Monitoring

The bot will log when manual intervention is needed:

```
🚨 CLOUDFLARE DETECTED! Please solve captcha manually via VNC.
VNC URL: http://your-unraid-ip:7900 (password: freebitcoin123)
Waiting up to 10 minutes for manual intervention...
```

## Troubleshooting

### Container Won't Start

- Check that all files are in the correct directory
- Verify `.env` file has correct values
- Check Unraid logs: `docker logs freebitcoin-bot`

### Cloudflare Keeps Appearing

- Try generating fresh cookies
- Clear browser data in VNC session
- Consider using a VPN or different IP

### VNC Connection Issues

- Ensure port 7900 is not blocked
- Try different VNC clients (TightVNC, RealVNC, etc.)
- Check container logs for VNC startup messages

## Unraid Template (Optional)

You can also create an Unraid template for easier management:

1. Go to Docker tab in Unraid
2. Add Container
3. Use these settings:
   - Repository: `selenium/standalone-chrome:131.0-20241225`
   - Ports: `7900:7900/tcp`, `4444:4444/tcp`
   - Volumes: `/mnt/user/appdata/freebitcoin-bot:/app`
   - Environment variables as needed

This setup gives you the best of both worlds: automation when possible, manual control when needed!
