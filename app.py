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

# Function to restart WebDriver
def restart_driver():
    global driver, SELENIUM_GRID_URL, chrome_options
    try:
        if driver:
            print("Restarting WebDriver...")
            driver.quit()
    except Exception as e:
        print(f"Error while quitting driver: {e}")
    driver = webdriver.Remote(command_executor=SELENIUM_GRID_URL, options=chrome_options)
    driver.maximize_window()
    return driver

# Load cookies from a file, if available
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

# Get remaining time
def get_remaining_time(driver):
    try:
        time_remaining_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "time_remaining"))
        )
        time_remaining_text = " ".join(time_remaining_element.text.split())
        match = re.search(r"(\d+)\s*Minutes.*?(\d+)\s*Seconds", time_remaining_text)
        if match:
            return int(match.group(1)) * 60 + int(match.group(2))
    except:
        print("Could not retrieve remaining time.")
    return 65 * 60  # Default to 65 minutes if not found

# Main execution loop
driver = restart_driver()
try:
    if not load_cookies(driver):
        login_with_retry(driver)

    while True:
        try:
            if click_play_without_captcha(driver):
                if click_roll_button(driver):
                    remaining_time = get_remaining_time(driver)
                    print(f"Waiting {remaining_time // 60} minutes and {remaining_time % 60} seconds.")
                    time.sleep(remaining_time)
                else:
                    print("Retrying 'Roll' button click.")
                    time.sleep(10)
            else:
                print("Retrying 'Play Without Captcha' button click.")
                time.sleep(10)
        except Exception as e:
            print(f"Error in main loop: {e}")
            driver = restart_driver()
except Exception as e:
    print(f"Critical error: {e}")
    if driver:
        driver.quit()
