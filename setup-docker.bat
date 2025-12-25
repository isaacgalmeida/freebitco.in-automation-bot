@echo off
echo 🚀 Setting up FreeBitco.in Bot for Docker...

REM Create logs directory if it doesn't exist
if not exist "logs" (
    mkdir logs
    echo ✅ Created logs directory
)

REM Check if .env file exists
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo ⚠️  Created .env from .env.example - please edit with your values
    ) else (
        echo ❌ No .env or .env.example file found!
        echo Please create .env with:
        echo TELEGRAM_TOKEN=your_bot_token
        echo TELEGRAM_CHAT_ID=your_chat_id
        echo HEADLESS=false
        echo CHROME_PATH=/usr/bin/google-chrome
        pause
        exit /b 1
    )
)

REM Check if cookies.json exists
if not exist "cookies.json" (
    echo ⚠️  No cookies.json found!
    echo You need to generate cookies first. Options:
    echo 1. Run locally: python getcookies.py
    echo 2. Use Docker: docker-compose -f docker-compose.production.yml --profile cookie-gen up cookie-generator
    echo    Then connect to VNC at http://localhost:7901 and run: python3 getcookies.py
)

REM Check required files
set missing=0
if not exist "app.py" (
    echo ❌ Missing app.py
    set missing=1
)
if not exist "CloudflareBypasser.py" (
    echo ❌ Missing CloudflareBypasser.py
    set missing=1
)
if not exist "requirements.txt" (
    echo ❌ Missing requirements.txt
    set missing=1
)

if %missing%==1 (
    echo Please ensure all required files are present
    pause
    exit /b 1
)

echo ✅ All required files present
echo.
echo 🐳 Ready to start! Use one of these commands:
echo.
echo # Start the bot:
echo docker-compose -f docker-compose.production.yml up -d
echo.
echo # Generate cookies (if needed):
echo docker-compose -f docker-compose.production.yml --profile cookie-gen up cookie-generator
echo.
echo # View logs:
echo docker-compose -f docker-compose.production.yml logs -f freebitcoin-bot
echo.
echo # VNC access: http://localhost:7900 (password: freebitcoin123)
echo.
pause