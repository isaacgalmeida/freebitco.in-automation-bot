import time 
import logging
import os
import json
import requests
import platform
import tempfile
from dotenv import load_dotenv
from CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions

# Load environment variables
load_dotenv()

def sleep_until(seconds):
    target = time.time() + seconds
    while time.time() < target:
        time.sleep(1)

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
    """Configure Chromium options for Docker environment."""
    options = ChromiumOptions()
    options.set_paths(browser_path=browser_path)
    for argument in arguments:
        options.set_argument(argument)

    # Enhanced stealth options for Docker
    options.set_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
    options.set_argument('--disable-blink-features=AutomationControlled')
    options.set_argument('--disable-infobars')
    options.set_argument('--disable-dev-shm-usage')
    options.set_argument('--no-sandbox')
    options.set_argument('--disable-gpu')
    options.set_argument('--disable-extensions')
    
    return options

def inject_cookies(driver, cookies_file, url):
    """Inject cookies into browser session."""
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

def is_cloudflare_challenge(driver):
    """Check if current page is a Cloudflare challenge."""
    try:
        title = driver.title.lower()
        page_source = driver.html.lower()
        
        cloudflare_indicators = [
            "just a moment",
            "checking your browser",
            "cloudflare",
            "please wait",
            "verifying you are human"
        ]
        
        return any(indicator in title or indicator in page_source for indicator in cloudflare_indicators)
    except Exception as e:
        logging.error(f"Error checking for Cloudflare: {e}")
        return False

def wait_for_manual_intervention(driver, max_wait_minutes=10):
    """Wait for manual captcha solving via VNC."""
    logging.warning("🚨 CLOUDFLARE DETECTED! Please solve captcha manually via VNC.")
    logging.warning(f"VNC URL: http://your-unraid-ip:7900 (password: your_vnc_password)")
    logging.warning(f"Waiting up to {max_wait_minutes} minutes for manual intervention...")
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    while time.time() - start_time < max_wait_seconds:
        if not is_cloudflare_challenge(driver):
            logging.info("✅ Cloudflare challenge resolved!")
            return True
        
        time.sleep(10)  # Check every 10 seconds
        remaining = max_wait_seconds - (time.time() - start_time)
        logging.info(f"Still waiting... {remaining/60:.1f} minutes remaining")
    
    logging.error("❌ Timeout waiting for manual intervention")
    return False

def close_popups(driver):
    """Close any popups or banners on the page."""
    try:
        popup = driver.ele('button:contains("NO THANKS")', timeout=3)
        if popup:
            popup.click()
            logging.info("Popup closed.")
    except Exception as e:
        logging.warning(f"No popup to close or error closing popup: {e}")

def click_roll_button(driver):
    """Click the 'Roll' button after resolving CAPTCHA."""
    try:
        roll_button = driver.ele('#free_play_form_button', timeout=10)
        if roll_button:
            roll_button.click()
            time.sleep(10)
            logging.info("Roll button clicked.")
            return True
        else:
            logging.warning("Roll button not found.")
            return False
    except Exception as e:
        logging.error(f"Roll button not found or not clickable: {e}")
        return False

def get_time_remaining(driver):
    """Get time remaining from the time_remaining div."""
    try:
        time_remaining_div = driver.ele('#time_remaining', timeout=10)
        if time_remaining_div:
            time_remaining_text = time_remaining_div.text.replace('\n', ' ')
            logging.info(f"Raw time_remaining text: {time_remaining_text}")
            
            if "Minutes" in time_remaining_text:
                minutes_part = time_remaining_text.split('Minutes')[0].strip()
                if minutes_part.isdigit():
                    minutes = int(minutes_part)
                    logging.info(f"Time remaining: {minutes} minutes.")
                    return minutes
                else:
                    logging.warning(f"Minutes part not valid: {minutes_part}")
            else:
                logging.warning("'Minutes' not found in time_remaining text.")
        else:
            logging.warning("time_remaining div not found.")
        return None
    except Exception as e:
        logging.error(f"Error getting time_remaining: {e}")
        return None

def send_balance_to_telegram(driver):
    """Send current balance and time remaining to Telegram."""
    try:
        balance = driver.ele("#balance", timeout=10).text
        time_remaining = driver.ele("#time_remaining", timeout=10).text.replace('\n', ' ')
        
        telegram_token = os.getenv("TELEGRAM_TOKEN")
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if telegram_token and telegram_chat_id:
            message = f"🤖 FreeBitco.in Bot Update\n💰 BTC Balance: {balance}\n⏰ Time Remaining: {time_remaining}"
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            requests.post(url, data={"chat_id": telegram_chat_id, "text": message})
            logging.info("Balance sent to Telegram.")
    except Exception as e:
        logging.error(f"Error sending balance to Telegram: {e}")

def check_internal_server_error(driver):
    """Check if page has 500 Internal Server Error."""
    try:
        time.sleep(5)
        page_source = driver.html
        
        if "Internal Server Error" in page_source or "500 Internal Server Error" in page_source:
            return True
    except Exception as e:
        logging.error(f"Error checking page status: {e}")
    return False

def main():
    isHeadless = os.getenv('HEADLESS', 'true').lower() == 'true'
    
    # Docker environment - use default Chrome path
    browser_path = "/usr/bin/google-chrome"
    
    base_arguments = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-extensions",
        "--disable-infobars",
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor",
        "--remote-debugging-port=9222",
        "--window-size=1920,1080"
    ]

    if isHeadless:
        base_arguments.append("--headless")

    while True:
        # Create temporary profile directory
        user_data_dir = tempfile.mkdtemp(prefix="drission_profile_")
        arguments = base_arguments.copy()
        arguments.append(f"--user-data-dir={user_data_dir}")
        
        options = get_chromium_options(browser_path, arguments)
        browser_closed = False
        
        try:
            driver = ChromiumPage(addr_or_opts=options)
            
            logging.info('Navigating to FreeBitco.in.')
            url = 'https://freebitco.in'
            driver.get(url)

            # Check for Cloudflare immediately
            if is_cloudflare_challenge(driver):
                if not wait_for_manual_intervention(driver):
                    logging.error("Failed to resolve Cloudflare challenge. Restarting...")
                    driver.quit()
                    browser_closed = True
                    sleep_until(300)  # Wait 5 minutes before retry
                    continue

            cookies_file = "cookies.json"
            if inject_cookies(driver, cookies_file, url):
                logging.info("Cookies applied successfully.")
            else:
                logging.warning("Could not apply cookies.")

            # Check for Cloudflare after cookie injection
            if is_cloudflare_challenge(driver):
                if not wait_for_manual_intervention(driver):
                    logging.error("Failed to resolve Cloudflare after cookies. Restarting...")
                    driver.quit()
                    browser_closed = True
                    sleep_until(300)
                    continue

            close_popups(driver)

            # Check for 500 error
            if check_internal_server_error(driver):
                logging.error("500 Internal Server Error detected. Waiting 10 minutes.")
                driver.quit()
                browser_closed = True
                sleep_until(600)
                continue

            time_remaining = get_time_remaining(driver)
            if time_remaining is not None:
                wait_time = (time_remaining + 1) * 60
                logging.info(f"Roll already done. Waiting {time_remaining + 1} minutes.")
                driver.quit()
                browser_closed = True
                sleep_until(wait_time)
                continue

            # Try Cloudflare bypasser first
            cf_bypasser = CloudflareBypasser(driver)
            cf_bypasser.click_verification_button()

            # Check if still blocked by Cloudflare
            time.sleep(5)
            if is_cloudflare_challenge(driver):
                if not wait_for_manual_intervention(driver):
                    logging.error("Could not resolve Cloudflare. Restarting...")
                    driver.quit()
                    browser_closed = True
                    sleep_until(300)
                    continue

            logging.info("Waiting 10 seconds before clicking Roll button.")
            time.sleep(10)

            if click_roll_button(driver):
                time_remaining = get_time_remaining(driver)
                if time_remaining is not None:
                    send_balance_to_telegram(driver)
                    wait_time = (time_remaining + 1) * 60
                    logging.info("Roll successful! Closing browser and waiting...")
                    driver.quit()
                    browser_closed = True
                    logging.info(f"Waiting {time_remaining + 1} minutes before next attempt.")
                    sleep_until(wait_time)
                    continue
                else:
                    logging.warning("Roll not completed successfully. Retrying...")
            else:
                logging.warning("Could not click Roll button. Retrying...")

        except Exception as e:
            logging.error("Error occurred: %s. Restarting browser...", str(e))
            time.sleep(5)

        finally:
            try:
                if not browser_closed:
                    logging.info('Closing browser.')
                    driver.quit()
            except Exception as cleanup_error:
                logging.error(f"Error during cleanup: {cleanup_error}")

if __name__ == '__main__':
    main()