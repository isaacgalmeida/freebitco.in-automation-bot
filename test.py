import time
import logging
import os
import json
import requests
from dotenv import load_dotenv
from CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cloudflare_bypass.log', mode='w')
    ]
)

def get_chromium_options(browser_path: str, arguments: list) -> ChromiumOptions:
    """
    Configures and returns Chromium options.
    """
    options = ChromiumOptions()
    options.set_paths(browser_path=browser_path)
    for argument in arguments:
        options.set_argument(argument)
    return options

def inject_cookies(driver, cookies_file, url):
    """
    Injects cookies into the browser session using the set.cookies() method.
    """
    if os.path.exists(cookies_file):
        try:
            with open(cookies_file, "r") as f:
                cookies = json.load(f)

            formatted_cookies = [
                f"name={cookie['name']}; value={cookie['value']}; domain={cookie['domain']}; path={cookie['path']};"
                for cookie in cookies
            ]

            driver.set.cookies(formatted_cookies)
            logging.info("Cookies injected successfully.")

            driver.get(url)
            logging.info("Page reloaded after applying cookies.")
            return True
        except Exception as e:
            logging.error(f"Error injecting cookies: {e}")
            return False
    else:
        logging.warning("Cookies file not found. Manual login required.")
        return False

def get_balance(driver):
    """
    Gets the BTC balance from the page.
    """
    try:
        balance_element = driver.ele("#balance", timeout=10)
        if balance_element:
            logging.info(f"BTC Balance found: {balance_element.text}")
            return balance_element.text
        else:
            logging.warning("Balance element not found.")
            return None
    except Exception as e:
        logging.error(f"Error getting balance: {e}")
        return None

def send_telegram_message(token, chat_id, message):
    """
    Sends a message to Telegram.
    """
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        response = requests.post(url, data=data)
        if response.status_code == 200:
            logging.info("Message sent to Telegram successfully.")
        else:
            logging.error(f"Error sending message to Telegram: {response.status_code}, {response.text}")
    except Exception as e:
        logging.error(f"Error sending message to Telegram: {e}")

def parse_time_remaining(time_remaining):
    """
    Extracts the number of minutes from the 'time_remaining' text.
    """
    try:
        # Assume format "XX Minutes YY Seconds"
        minutes = int(time_remaining.split("Minutes")[0].strip())
        return minutes
    except Exception as e:
        logging.error(f"Error parsing 'time_remaining': {e}")
        return None

def check_time_remaining_and_send(driver):
    """
    Checks if 'time_remaining' div is present. If yes, sends balance and time remaining to Telegram.
    """
    try:
        time_remaining_div = driver.ele('#time_remaining', timeout=10)
        if time_remaining_div:
            # Remove line breaks and process the text
            time_remaining = time_remaining_div.text.replace('\n', ' ')
            balance = get_balance(driver)

            telegram_token = os.getenv("TELEGRAM_TOKEN")
            telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

            if telegram_token and telegram_chat_id:
                if balance and time_remaining:
                    message = f"BTC Balance: {balance}\nTime Remaining: {time_remaining}"
                elif balance:
                    message = f"BTC Balance: {balance}\nTime Remaining: Not available."
                else:
                    message = "Unable to retrieve BTC balance or time remaining."
                send_telegram_message(telegram_token, telegram_chat_id, message)

            # Parse time_remaining to extract minutes
            minutes = parse_time_remaining(time_remaining)
            if minutes is not None:
                wait_time = (minutes + 3) * 60
                logging.info(f"Waiting {minutes + 3} minutes before retrying.")
            else:
                wait_time = 63 * 60
                logging.info("Could not parse 'time_remaining'. Waiting 63 minutes by default.")

            time.sleep(wait_time)
            return True
        else:
            return False
    except Exception as e:
        logging.error(f"Error checking 'time_remaining': {e}")
        return False

def main():
    isHeadless = os.getenv('HEADLESS', 'false').lower() == 'true'
    
    if isHeadless:
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(1920, 1080))
        display.start()

    browser_path = os.getenv('CHROME_PATH', "/usr/bin/google-chrome")

    arguments = [
        "-no-first-run",
        "-force-color-profile=srgb",
        "-metrics-recording-only",
        "-password-store=basic",
        "-use-mock-keychain",
        "-export-tagged-pdf",
        "-no-default-browser-check",
        "-disable-background-mode",
        "-enable-features=NetworkService,NetworkServiceInProcess,LoadCryptoTokenExtension,PermuteTLSExtensions",
        "-disable-features=FlashDeprecationWarning,EnablePasswordsAccountStorage",
        "-deny-permission-prompts",
        "-disable-gpu",
        "-accept-lang=en-US",
    ]

    options = get_chromium_options(browser_path, arguments)

    while True:
        driver = ChromiumPage(addr_or_opts=options)
        try:
            logging.info('Navigating to FreeBitco.in.')
            url = 'https://freebitco.in'
            driver.get(url)

            cookies_file = "cookies.json"
            if inject_cookies(driver, cookies_file, url):
                logging.info("Cookies applied. Automatic login successful.")
            else:
                logging.warning("Cookies could not be applied. Please check your cookies.json file.")

            # Check if 'time_remaining' div is already present
            if check_time_remaining_and_send(driver):
                continue  # Restart loop after waiting

            cf_bypasser = CloudflareBypasser(driver)
            cf_bypasser.click_verification_button()

            # Wait 10 seconds before clicking the 'Roll' button
            logging.info("Waiting 10 seconds before clicking 'Roll' button.")
            time.sleep(10)

            # Click the Roll button
            roll_button = driver.ele('#free_play_form_button', timeout=30)
            if roll_button:
                roll_button.click()
                logging.info("Clicked 'Roll' button.")

                # Check if 'time_remaining' appears after clicking the button
                if check_time_remaining_and_send(driver):
                    continue
                else:
                    logging.warning("Roll did not complete successfully.")
            else:
                logging.warning("Could not find 'Roll' button.")

        except Exception as e:
            logging.error("An error occurred: %s", str(e))
        finally:
            logging.info('Closing the browser.')
            driver.quit()
            if isHeadless:
                display.stop()

if __name__ == '__main__':
    main()
