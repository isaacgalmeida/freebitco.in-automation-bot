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
from selenium.common.exceptions import WebDriverException, TimeoutException, InvalidSessionIdException

# User agents for randomization
# user_agents = [
#     'HTC: Mozilla/5.0 (Linux; Android 7.0; HTC 10 Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.83 Mobile Safari/537.36',
#     'Google Nexus: Mozilla/5.0 (Linux; U; Android-4.0.3; en-us; Galaxy Nexus Build/IML74K) AppleWebKit/535.7 (KHTML, like Gecko) CrMo/16.0.912.75 Mobile Safari/535.7',
# ]
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36',  # Chrome Windows
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36',  # Chrome Mac
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0',  # Firefox Windows
    'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Mobile Safari/537.36',  # Chrome Android
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',  # Safari iPhone
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
chrome_options.add_argument("--window-size=1920,1080")  # Ensure larger viewport

# Initialize driver as a global variable
driver = None

# Restart WebDriver
def restart_driver():
    global driver, SELENIUM_GRID_URL, chrome_options
    try:
        if driver:
            try:
                driver.quit()
            except WebDriverException:
                pass
        driver = webdriver.Remote(command_executor=SELENIUM_GRID_URL, options=chrome_options)
        driver.maximize_window()
        return driver
    except WebDriverException as e:
        raise RuntimeError(f"Failed to start WebDriver: {e}")

# Load cookies from file
def load_cookies(driver):
    try:
        if os.path.exists('cookies.json'):
            with open('cookies.json', 'r') as file:
                cookies = json.load(file)
            driver.get("https://freebitco.in")
            for cookie in cookies:
                driver.add_cookie(cookie)
            driver.refresh()
            print("Cookies loaded and page refreshed.")
            time.sleep(10)
            return True
        else:
            print("Cookies file not found. Login required.")
            return False
    except Exception as e:
        print(f"Error loading cookies: {e}")
        return False

# Save cookies to file
def save_cookies(driver):
    try:
        with open('cookies.json', 'w') as file:
            json.dump(driver.get_cookies(), file)
        print("Cookies saved successfully.")
    except Exception as e:
        print(f"Error saving cookies: {e}")

# Perform login
def login_with_retry(driver):
    url = 'https://freebitco.in/signup/?op=s'
    driver.get(url)
    while True:
        try:
            email_field = WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.ID, 'login_form_btc_address'))
            )
            password_field = WebDriverWait(driver, 15).until(
                EC.visibility_of_element_located((By.ID, 'login_form_password'))
            )

            email = os.getenv("EMAIL")
            password = os.getenv("PASSWORD")

            email_field.clear()
            email_field.send_keys(email)
            password_field.clear()
            password_field.send_keys(password)

            login_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "login_button"))
            )
            login_button.click()
            print("Login form submitted.")

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'play_without_captchas_button'))
            )
            print("Login successful.")
            save_cookies(driver)
            break
        except TimeoutException:
            print("Timeout occurred during login. Retrying...")
        except Exception as e:
            print(f"Error during login attempt: {e}. Retrying...")
            time.sleep(random.randint(60, 180))

# Handle time remaining
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
            return remaining_time
    except Exception as e:
        print(f"Could not determine time remaining: {e}")
    return 3900  # Default wait time (65 minutes)

# Click the "Roll" button
def click_roll_button(driver):
    try:
        roll_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "free_play_form_button"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", roll_button)
        roll_button.click()
        print("Clicked 'Roll' button.")
        return True
    except Exception as e:
        print(f"'Roll' button not found: {e}")
        return False

# Main execution loop
try:
    while True:
        driver = restart_driver()
        if not load_cookies(driver):
            login_with_retry(driver)

        if click_roll_button(driver):
            print("Roll successful. Closing browser after 3 seconds.")
            time.sleep(60)
            driver.quit()
        else:
            print("Roll button not available. Checking remaining time...")
            remaining_time = handle_time_remaining(driver)
            driver.quit()
            print(f"Waiting {remaining_time} seconds before reopening browser.")
            time.sleep(remaining_time)
except InvalidSessionIdException as e:
    print(f"Session lost: {e}. Restarting driver.")
    driver = restart_driver()
except Exception as e:
    print(f"Critical error: {e}")
finally:
    if driver:
        try:
            driver.quit()
        except WebDriverException as e:
            print(f"Error quitting driver: {e}")
