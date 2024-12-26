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
import requests  # Lembre-se de importar requests para o send_telegram_message
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    InvalidSessionIdException
)

# =============== CONFIGURAÇÕES GERAIS ===============

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36',  # Chrome Windows
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36',  # Chrome Mac
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0',  # Firefox Windows
    'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Mobile Safari/537.36',  # Chrome Android
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',  # Safari iPhone
]
random_user_agent = random.choice(user_agents)

load_dotenv()

SELENIUM_GRID_URL = os.getenv('SELENIUM_GRID_URL', 'http://localhost:4444/wd/hub')

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--dns-server=8.8.8.8')
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument(f"user-agent={random_user_agent}")
chrome_options.add_experimental_option(
    "prefs", {"profile.default_content_setting_values.notifications": 2}
)
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument("--start-maximized")

driver = None

# Armazena o timestamp do último alerta diário enviado.
last_daily_alert_time = 0


# =============== FUNÇÕES AUXILIARES ===============

# Exemplo de como obter o saldo na página (ajuste conforme o ID real do elemento de saldo)
def get_balance(driver):
    try:
        # Exemplo: se o elemento do saldo tiver ID "balance" ou algo assim
        balance_element = driver.find_element(By.ID, "balance")
        return balance_element.text
    except Exception:
        return None

# Envia mensagem para Telegram
def send_telegram_message(token, chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("Message sent to Telegram successfully.")
        else:
            print(f"Error sending message to Telegram: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")

# Envia o saldo atual para Telegram
def send_balance_to_telegram(driver):
    balance = get_balance(driver)
    if balance:
        message = f"BTC Balance (freebitco): {balance}"
        telegram_token = os.getenv("TELEGRAM_TOKEN")
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if telegram_token and telegram_chat_id:
            send_telegram_message(telegram_token, telegram_chat_id, message)

# Checa se passaram 24 horas desde o último alerta e, se sim, envia saldo para Telegram
def check_and_send_daily_balance(driver):
    global last_daily_alert_time
    # 24 horas em segundos
    daily_interval = 24 * 60 * 60

    # Se a diferença entre agora e o último envio >= 24h, envia o alerta
    if (time.time() - last_daily_alert_time) >= daily_interval:
        send_balance_to_telegram(driver)
        last_daily_alert_time = time.time()

def force_click(driver, element):
    """
    Faz scroll para o elemento e usa JavaScript para clicar,
    evitando erros de 'element click intercepted'.
    """
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    time.sleep(1)  # Pequena pausa para garantir o scroll
    driver.execute_script("arguments[0].click();", element)

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

def save_cookies(driver):
    try:
        with open('cookies.json', 'w') as file:
            json.dump(driver.get_cookies(), file)
        print("Cookies saved successfully.")
    except Exception as e:
        print(f"Error saving cookies: {e}")

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
            force_click(driver, login_button)
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

def click_play_without_captcha(driver):
    try:
        play_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'play_without_captchas_button'))
        )
        force_click(driver, play_btn)
        print("Clicked 'play_without_captchas_button'. Waiting 3 seconds...")
        time.sleep(3)
    except TimeoutException:
        print("play_without_captchas_button not found. Skipping.")
    except Exception as e:
        print(f"Error clicking 'play_without_captchas_button': {e}")

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
    return 3900  # Se não conseguir achar, espera 65 minutos

def click_roll_button(driver):
    try:
        roll_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.ID, "free_play_form_button"))
        )
        force_click(driver, roll_button)
        print("Clicked 'Roll' button.")
        return True
    except Exception as e:
        print(f"'Roll' button not found or not clickable: {e}")
        return False

def confirm_roll_and_refresh_if_needed(driver, max_attempts=3):
    attempt = 0
    while attempt < max_attempts:
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "time_remaining"))
            )
            return True
        except TimeoutException:
            attempt += 1
            print(f"time_remaining not found. Refreshing page (attempt {attempt}/{max_attempts}).")
            driver.refresh()
    return False


# =============== LOOP PRINCIPAL ===============
try:
    while True:
        driver = restart_driver()

        # Se não conseguir carregar cookies, faz login
        if not load_cookies(driver):
            login_with_retry(driver)

        # Checa se devemos enviar o alerta diário (a cada 24h)
        check_and_send_daily_balance(driver)

        # Envia o saldo atual toda vez que entra no loop (já existia no código)
        send_balance_to_telegram(driver)

        # Clica no botão 'play_without_captchas_button' antes de 'Roll'
        click_play_without_captcha(driver)

        # Tenta clicar no botão "Roll"
        if click_roll_button(driver):
            # Verifica se o 'time_remaining' aparece, recarregando se necessário
            if confirm_roll_and_refresh_if_needed(driver):
                print("Roll successful. Closing browser after 3 seconds.")
            else:
                print("Could not confirm 'time_remaining' after multiple attempts.")

            # Aguarda 60s antes de fechar o navegador
            time.sleep(60)
            try:
                driver.quit()
            except WebDriverException:
                pass
        else:
            print("Roll button not available. Checking remaining time...")
            remaining_time = handle_time_remaining(driver)
            try:
                driver.quit()
            except WebDriverException:
                pass
            print(f"Waiting {remaining_time} seconds before reopening browser.")
            time.sleep(remaining_time)

except InvalidSessionIdException as e:
    print(f"Session lost: {e}.")
    try:
        driver.quit()
    except WebDriverException:
        pass
    driver = restart_driver()

except Exception as e:
    print(f"Critical error: {e}")
    try:
        driver.quit()
    except WebDriverException as ex:
        print(f"Error quitting driver after exception: {ex}")

finally:
    if driver:
        try:
            driver.quit()
        except WebDriverException as e:
            print(f"Error quitting driver (final block): {e}")
