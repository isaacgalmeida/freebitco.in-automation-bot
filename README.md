### README.md

````markdown
# Freebitco.in Automation Bot

This is a Python Selenium-based bot designed to automate interactions with the Freebitco.in website. The bot can perform actions like logging in, handling cookies, clicking the "Roll" button, and waiting for the next roll time.

## Features

- Automatically logs in using saved cookies or credentials.
- Handles the "Too many tries" error by waiting the required time before retrying.
- Clicks the "Roll" button and waits for the cooldown period.
- Continuous operation in a loop.

## Requirements

- Python 3.7+
- Docker and Docker Compose (to run Selenium Chrome container)
- Selenium WebDriver
- ChromeDriver or Selenium Grid setup

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/freebitco-automation-bot.git
   cd freebitco-automation-bot
   ```
````

2. Set up a Python virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory and add your login credentials and Selenium Grid URL:

   ```env
   EMAIL=your-email@example.com
   PASSWORD=your-password
   SELENIUM_GRID_URL=http://localhost:4444/wd/hub
   ```

5. Configure and start Selenium Chrome using Docker Compose.

## Starting Selenium Chrome

To run the bot, you first need to start a Selenium Chrome container. Use the provided `compose.yml` file:

### Step 1: Create the Docker Compose File

Create a `compose.yml` file in the root directory with the following content:

```yaml
services:
  selenium-chrome:
    image: selenium/standalone-chrome:131.0
    container_name: selenium-chrome
    ports:
      - "4444:4444" # Port for WebDriver
      - "7900:7900" # Port for VNC
    shm_size: "2g" # Shared memory size
    restart: unless-stopped
```

### Step 2: Start the Selenium Chrome Container

Run the following command to start the container:

```bash
docker-compose up -d
```

This will:

- Make Selenium WebDriver available at `http://localhost:4444/wd/hub`.
- Expose a VNC interface at `http://localhost:7900` (useful for debugging).

For more details, refer to the [official Selenium Chrome Docker image documentation](https://hub.docker.com/r/selenium/standalone-chrome).

## Usage

Run the bot:

```bash
python3 app.py
```

The bot will:

1. Attempt to load cookies to log in without needing credentials.
2. Log in using the `.env` credentials if cookies are not found or invalid.
3. Continuously check for the "Roll" button and click it when available.
4. Wait for the cooldown period and repeat.

## Notes

- Make sure the `cookies.json` file is writable. The bot saves cookies after a successful login.
- Adjust the Selenium Remote WebDriver URL in the `.env` file if using a different setup for Selenium.
- To debug browser interactions, you can connect to the VNC interface exposed on port `7900`.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

```

```
