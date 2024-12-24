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

# Initialize WebDriver
driver = webdriver.Remote(
    command_executor=SELENIUM_GRID_URL,
    options=chrome_options
)

# Maximize the browser window
driver.maximize_window()

# Load cookies from a file, if available
def load_cookies(driver):
    try:
        with open('cookies.json', 'r') as file:
            cookies = json.load(file)
        driver.get("https://freebitco.in")
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.refresh()  # Refresh the page to apply cookies
        print("Cookies loaded and page refreshed.")

        # Wait for 10 seconds to check if Play Without Captcha button is present
        time.sleep(10)
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, 'time_remaining'))
            )
            print("Cookies were sufficient. No login required.")
            return True
        except:
            print("Cookies were not sufficient. Login required.")
            return False
    except FileNotFoundError:
        print("Cookies file not found. Login required.")
        return False

# Save cookies to a file after login
def save_cookies(driver):
    try:
        with open('cookies.json', 'w') as file:
            json.dump(driver.get_cookies(), file)
        print("Cookies saved successfully.")
    except Exception as e:
        print(f"Error saving cookies: {e}")

# Perform login and retry logic
def login_with_retry(driver):
    url = 'https://freebitco.in/signup/?op=s'
    driver.get(url)
    while True:
        try:
            # Input email and password
            email_field = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, 'login_form_btc_address'))
            )
            password_field = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, 'login_form_password'))
            )

            # Clear fields before entering new values
            email_field.clear()
            password_field.clear()

            email = os.getenv("EMAIL")
            password = os.getenv("PASSWORD")
            email_field.send_keys(email)
            password_field.send_keys(password)

            # Submit the login form
            login_form_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "login_button"))
            )
            driver.execute_script("arguments[0].click();", login_form_button)
            print("Login form submitted.")

            # Check if Play Without Captcha button exists
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'play_without_captchas_button'))
                )
                print("Login successful. Play Without Captcha button is available.")
                save_cookies(driver)  # Save cookies after successful login
                break
            except:
                print("Login unsuccessful. Retrying in a few minutes.")
                wait_time = random.randint(60, 180)  # Wait between 1 to 3 minutes
                print(f"Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
        except Exception as e:
            print(f"Error during login attempt: {e}")

# Click the "Play Without Captcha" button
def click_play_without_captcha(driver):
    try:
        play_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "play_without_captchas_button"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", play_button)
        driver.execute_script("arguments[0].click();", play_button)
        print("Play Without Captcha Button clicked.")
        return True
    except Exception as e:
        print(f"Play Without Captcha Button not found or not clickable: {e}")
        return False

# Click the "Roll" button
def click_roll_button(driver):
    try:
        roll_button_element = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "free_play_form_button"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", roll_button_element)
        driver.execute_script("arguments[0].click();", roll_button_element)
        print("Roll Button clicked.")
        return True
    except Exception as e:
        print(f"Roll Button not found or not clickable: {e}")
        return False

# Get remaining time for next roll
def get_remaining_time(driver):
    try:
        time_remaining_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "time_remaining"))
        )
        time_remaining_text = time_remaining_element.text
        print(f"Time remaining for next roll: {time_remaining_text}")
        match = re.search(r"(\d+)\s*Minutes.*?(\d+)\s*Seconds", time_remaining_text)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            return minutes * 60 + seconds
    except:
        print("Could not get remaining time. Using default of 65 minutes.")
        return 65 * 60

# Main execution loop
try:
    if not load_cookies(driver):
        login_with_retry(driver)

    while True:
        if click_play_without_captcha(driver):
            if click_roll_button(driver):
                remaining_time = get_remaining_time(driver)
                print(f"Roll successful. Waiting {remaining_time // 60} minutes and {remaining_time % 60} seconds for the next attempt.")
                time.sleep(remaining_time)
            else:
                print("Retrying Roll button click.")
                time.sleep(10)
        else:
            print("Retrying Play Without Captcha button click.")
            time.sleep(10)
except Exception as e:
    print(f"Critical error occurred: {e}")
finally:
    driver.quit()
