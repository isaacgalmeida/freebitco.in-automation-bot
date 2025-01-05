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

def close_popups(driver):
    """
    Closes any popups or banners on the page.
    """
    try:
        popup = driver.ele('button:contains("NO THANKS")', timeout=3, show_errmsg=False)
        if popup:
            popup.click()
            logging.info("Popup closed.")
    except Exception as e:
        logging.warning(f"No popup to close or error closing popup: {e}")

def click_roll_button(driver):
    """
    Clicks the 'Roll' button after resolving the CAPTCHA.
    """
    try:
        roll_button = driver.ele('#free_play_form_button', timeout=10)
        if roll_button:
            roll_button.click()
            time.sleep(10)
            logging.info("Clicked 'Roll' button.")
            return True
        else:
            logging.warning("'Roll' button not found.")
            return False
    except Exception as e:
        logging.error(f"'Roll' button not found or not clickable: {e}")
        return False

def get_time_remaining(driver):
    """
    Retrieves the time remaining from the 'time_remaining' div.
    """
    try:
        time_remaining_div = driver.ele('#time_remaining', timeout=10)
        if time_remaining_div:
            time_remaining_text = time_remaining_div.text.replace('\n', ' ')
            logging.info(f"Raw time_remaining text: {time_remaining_text}")
            
            if "Minutes" in time_remaining_text:
                minutes_part = time_remaining_text.split('Minutes')[0].strip()
                if minutes_part.isdigit():
                    minutes = int(minutes_part)
                    logging.info(f"Extracted time remaining: {minutes} minutes.")
                    return minutes
                else:
                    logging.warning(f"Minutes part is not a valid integer: {minutes_part}")
            else:
                logging.warning("'Minutes' keyword not found in time_remaining text.")
        else:
            logging.warning("'time_remaining' div not found.")
        return None
    except Exception as e:
        logging.error(f"Error getting 'time_remaining': {e}")
        return None

def send_balance_to_telegram(driver):
    """
    Sends the current balance and time remaining to Telegram.
    """
    try:
        balance = driver.ele("#balance", timeout=10).text
        time_remaining = driver.ele("#time_remaining", timeout=10).text.replace('\n', ' ')

        telegram_token = os.getenv("TELEGRAM_TOKEN")
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if telegram_token and telegram_chat_id:
            message = f"BTC Balance: {balance}\nTime Remaining: {time_remaining}"
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            requests.post(url, data={"chat_id": telegram_chat_id, "text": message})
            logging.info("Balance and time remaining sent to Telegram.")
    except Exception as e:
        logging.error(f"Error sending balance to Telegram: {e}")

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
        "--remote-debugging-port=9222"  # Ensure this line is included
    ]

    options = get_chromium_options(browser_path, arguments)

    while True:
        try:
            driver = ChromiumPage(addr_or_opts=options)
            logging.info('Navigating to FreeBitco.in.')
            url = 'https://freebitco.in'
            driver.get(url)

            cookies_file = "cookies.json"
            if inject_cookies(driver, cookies_file, url):
                logging.info("Cookies applied. Automatic login successful.")
            else:
                logging.warning("Cookies could not be applied. Please check your cookies.json file.")

            # Close any popups
            close_popups(driver)

            # Check if the 'time_remaining' div is present
            time_remaining = get_time_remaining(driver)
            if time_remaining is not None:
                wait_time = (time_remaining + 1) * 60
                logging.info(f"Waiting {time_remaining + 1} minutes before retrying.")
                time.sleep(wait_time)
                continue

            # Resolve CAPTCHA and click 'Roll'
            cf_bypasser = CloudflareBypasser(driver)
            cf_bypasser.click_verification_button()

            logging.info("Waiting 10 seconds before clicking 'Roll' button.")
            time.sleep(10)

            if click_roll_button(driver):
                time_remaining = get_time_remaining(driver)
                if time_remaining is not None:
                    send_balance_to_telegram(driver)
                    wait_time = (time_remaining + 1) * 60
                    logging.info(f"Roll successful. Waiting {time_remaining + 1} minutes before retrying.")
                    time.sleep(wait_time)
                else:
                    logging.warning("Roll did not complete successfully. Retrying...")
            else:
                logging.warning("Could not click 'Roll' button. Retrying...")
        except Exception as e:
            logging.error("An error occurred: %s. Restarting browser...", str(e))
            time.sleep(5)  # Wait before restarting
        finally:
            try:
                logging.info('Closing the browser.')
                driver.quit()
                if isHeadless:
                    display.stop()
            except Exception as cleanup_error:
                logging.error(f"Error during browser cleanup: {cleanup_error}")

if __name__ == '__main__':
    main()
