# Function to click the "Play Without Captcha" button
def click_play_without_captcha(driver):
    try:
        # Wait for the "Play Without Captcha" button to appear and be clickable
        play_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'PLAY WITHOUT CAPTCHA')]"))
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
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'ROLL!')]"))
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
    if not load_cookies(driver) or is_login_required(driver):
        login(driver)

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
