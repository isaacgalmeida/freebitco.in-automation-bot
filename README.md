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

4. Create a `.env` file in the root directory and add your login credentials:

   ```env
   EMAIL=your-email@example.com
   PASSWORD=your-password
   ```

5. Ensure you have ChromeDriver installed or a Selenium Grid URL. Update the Selenium Remote WebDriver URL in the script if necessary.

## Usage

Run the bot:

```bash
python app.py
```

The bot will:

1. Attempt to load cookies to log in without needing credentials.
2. Log in using the `.env` credentials if cookies are not found or invalid.
3. Continuously check for the "Roll" button and click it when available.
4. Wait for the cooldown period and repeat.

## Notes

- Make sure the `cookies.json` file is writable. The bot saves cookies after a successful login.
- Adjust the Selenium Remote WebDriver URL if using a different setup for Selenium.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

```

```
