from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import json
from dotenv import load_dotenv
import os
import re
import threading
from selenium.common.exceptions import WebDriverException, NoSuchElementException

# User agents for randomization
user_agents = [
    'HTC: Mozilla/5.0 (Linux; Android 7.0; HTC 10 Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.83 Mobile Safari/537.36',
    'Google Nexus: Mozilla/5.0 (Linux; U; Android-4.0.3; en-us; Galaxy Nexus Build/IML74K) AppleWebKit/535.7 (KHTML, like Gecko) CrMo/16.0.912.75 Mobile Safari/535.7',
]

# Choose a random user agent
random_user_agent = random.choice(user_agents)

# Load environment variables
load_dotenv()

# Get Selenium Grid URL from .env
SELENIUM_GRID_URL = os.getenv('SELENIUM_GRID_URL', 'http://localhost:4444/wd/hub')  # Default to localhost

# Set Chrome options
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--dns-server=8.8.8.8')
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument(f"user-agent={random_user_agent}")
chrome_options.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 2})

# Initialize driver as a global variable
driver = None

# Function to restart WebDriver with retries
def restart_driver(retries=5, delay=10):
    global driver, SELENIUM_GRID_URL, chrome_options
    for attempt in range(retries):
        try:
            print(f"Attempt {attempt + 1} to start WebDriver...")
            if driver:
                driver.quit()
            driver = webdriver.Remote(command_executor=SELENIUM_GRID_URL, options=chrome_options)
            driver.maximize_window()
            return driver
        except WebDriverException as e:
            print(f"Error starting WebDriver: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
    raise RuntimeError("Failed to start WebDriver after multiple retries.")

# Check and restart session if lost
def check_session_and_restart(driver):
    try:
        driver.title  # Try to access the browser
    except WebDriverException as e:
        if "Cannot find session" in str(e):
            print("Session lost. Restarting WebDriver...")
            return restart_driver()
        else:
            raise
    return driver

# Load cookies from a file
def load_cookies(driver):
    try:
        with open('cookies.json', 'r') as file:
            cookies = json.load(file)
        driver.get("https://freebitco.in")
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.refresh()
        print("Cookies loaded and page refreshed.")
        time.sleep(10)
        return True
    except FileNotFoundError:
        print("Cookies file not found. Login required.")
        return False

# Save cookies to a file
def save_cookies(driver):
    try:
        with open('cookies.json', 'w') as file:
            json.dump(driver.get_cookies(), file)
        print("Cookies saved successfully.")
    except Exception as e:
        print(f"Error saving cookies: {e}")

# Perform login with retries
def login_with_retry(driver):
    url = 'https://freebitco.in/signup/?op=s'
    driver.get(url)
    while True:
        try:
            email_field = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, 'login_form_btc_address'))
            )
            password_field = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, 'login_form_password'))
            )

            email_field.clear()
            password_field.clear()
            email = os.getenv("EMAIL")
            password = os.getenv("PASSWORD")
            email_field.send_keys(email)
            password_field.send_keys(password)

            login_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "login_button"))
            )
            driver.execute_script("arguments[0].click();", login_button)
            print("Login form submitted.")

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'play_without_captchas_button'))
                )
                print("Login successful.")
                save_cookies(driver)
                break
            except:
                print("Login failed. Retrying...")
                time.sleep(random.randint(60, 180))
        except Exception as e:
            print(f"Error during login attempt: {e}")

# Click "Play Without Captcha"
def click_play_without_captcha(driver):
    try:
        play_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "play_without_captchas_button"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", play_button)
        driver.execute_script("arguments[0].click();", play_button)
        print("Clicked 'Play Without Captcha' button.")
        return True
    except Exception as e:
        print(f"'Play Without Captcha' button not found: {e}")
        return handle_time_remaining(driver)

# Extract and handle time remaining
def handle_time_remaining(driver):
    try:
        time_remaining_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "time_remaining"))
        )
        time_remaining_text = " ".join(time_remaining_element.text.split())
        print(f"Time remaining for next roll: {time_remaining_text}")
        match = re.search(r"(\d+)\s*Minutes.*?(\d+)\s*Seconds", time_remaining_text)
        if match:
            remaining_time = int(match.group(1)) * 60 + int(match.group(2))
            print(f"Waiting {remaining_time // 60} minutes and {remaining_time % 60} seconds before retrying.")
            time.sleep(remaining_time)
            return False
    except Exception as inner_e:
        print(f"Could not determine time remaining: {inner_e}")
    return False

# Click the "Roll" button
def click_roll_button(driver):
    try:
        roll_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "free_play_form_button"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", roll_button)
        driver.execute_script("arguments[0].click();", roll_button)
        print("Clicked 'Roll' button.")
        return True
    except Exception as e:
        print(f"'Roll' button not found: {e}")
        return False

# Keep session alive
def keep_session_alive(driver, interval=300):
    while True:
        try:
            time.sleep(interval)
            driver.execute_script("return navigator.userAgent;")
            print("Heartbeat sent to keep session active.")
        except Exception as e:
            print(f"Error in heartbeat: {e}")
            break

# Main execution loop
driver = restart_driver()

# Start heartbeat thread
heartbeat_thread = threading.Thread(target=keep_session_alive, args=(driver,), daemon=True)
heartbeat_thread.start()

try:
    if not load_cookies(driver):
        login_with_retry(driver)

    while True:
        try:
            driver = check_session_and_restart(driver)
            if click_play_without_captcha(driver):
                if click_roll_button(driver):
                    print("Roll successful. Waiting for the next round.")
                    time.sleep(3600)
                else:
                    print("Retrying 'Roll' button click.")
                    time.sleep(10)
            else:
                print("Retrying 'Play Without Captcha' button click.")
        except Exception as e:
            print(f"Error in main loop: {e}")
            driver = restart_driver()
except Exception as e:
    print(f"Critical error: {e}")
    if driver:
        driver.quit()
