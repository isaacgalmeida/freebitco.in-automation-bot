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
        
        # Check if login is still required after refreshing
        if is_login_required(driver):
            print("Cookies were not sufficient. Login required.")
            return False
        else:
            print("Cookies were sufficient. No login required.")
            return True
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

# Function to handle the "Too Many Tries" message and wait
def handle_too_many_tries(driver):
    try:
        # Wait for the error message to appear
        error_message_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Too many tries')]"))
        )
        error_message_text = error_message_element.text
        print(f"Error message detected: {error_message_text}")
        
        # Extract the time to wait from the error message using regex
        match = re.search(r"wait (\d+) (seconds|minutes)", error_message_text)
        if match:
            wait_time = int(match.group(1))
            unit = match.group(2)
            if unit == "minutes":
                wait_time *= 60  # Convert minutes to seconds
            print(f"Waiting for {wait_time} seconds before retrying...")
            time.sleep(wait_time)
        else:
            print("Could not extract wait time from error message. Retrying in 30 seconds.")
            time.sleep(30)
    except Exception as e:
        print(f"Error while handling 'Too many tries' message: {e}")
        time.sleep(30)  # Default wait time if error handling fails

# Perform login, retrying if "Too Many Tries" is encountered
def login(driver):
    url = 'https://freebitco.in/signup/?op=s'
    driver.get(url)
    try:
        # Click the Login button
        login_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//a[text()='LOGIN']"))
        )
        driver.execute_script("arguments[0].click();", login_button)
        print("Login button clicked.")

        while True:
            try:
                # Input email and password
                email_field = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.ID, 'login_form_btc_address'))
                )
                password_field = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.ID, 'login_form_password'))
                )

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
                break  # Exit the loop if login is successful
            except Exception as e:
                # Check for "Too many tries" message and handle it
                print("Login attempt failed. Checking for 'Too many tries' message...")
                handle_too_many_tries(driver)

        # Save cookies after successful login
        save_cookies(driver)
    except Exception as e:
        print(f"Error during login: {e}")

# Function to check if login is still required
def is_login_required(driver):
    try:
        # Check for the presence of the "LOGIN" button
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//a[text()='LOGIN']"))
        )
        return True  # Login button found, login is required
    except:
        return False  # Login button not found, login is not required

# Function to click the "Play Without Captcha" button
def click_play_without_captcha(driver):
    try:
        # Wait for the "Play Without Captcha" button to appear and be clickable
        play_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "play_without_captcha_button"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", play_button)  # Scroll to the button
        driver.execute_script("arguments[0].click();", play_button)  # Click using JavaScript
        print("Play Without Captcha Button clicked.")
        return True
    except Exception as e:
        print(f"Play Without Captcha Button not found or not clickable: {e}")
        return False

# Function to click the "Roll" button
def click_roll_button(driver):
    try:
        # Ensure the button is visible
        roll_button_element = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "free_play_form_button"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", roll_button_element)  # Scroll to the button
        driver.execute_script("arguments[0].click();", roll_button_element)  # Click using JavaScript
        print("Roll Button clicked.")
        return True
    except Exception as e:
        print(f"Roll Button not found or not clickable: {e}")
        return False

# Main execution loop
try:
    # Load cookies and check if login is required
    if not load_cookies(driver):
        login(driver)  # Perform login if cookies are not sufficient

    while True:
        # Try clicking the "Play Without Captcha" button first
        if click_play_without_captcha(driver):
            # After clicking "Play Without Captcha", attempt to click the "Roll" button
            if click_roll_button(driver):
                print("Roll successful. Waiting for the next attempt.")
                time.sleep(3600)  # Wait 1 hour before the next attempt
            else:
                print("Retrying Roll button click.")
                time.sleep(10)
        else:
            print("Retrying Play Without Captcha button click.")
            time.sleep(10)
except Exception as e:
    print(f"Critical error occurred: {e}")
finally:
    # Close the browser in case of an error or shutdown
    driver.quit()
