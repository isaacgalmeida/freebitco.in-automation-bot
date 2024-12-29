import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()

def inject_cookies(driver, cookies_file, url):
    """
    Injeta cookies para login no site e atualiza a página.
    """
    driver.get(url)
    if os.path.exists(cookies_file):
        try:
            with open(cookies_file, "r") as f:
                cookies = json.load(f)

            for cookie in cookies:
                driver.add_cookie(cookie)

            driver.refresh()
            print("Cookies injetados com sucesso e página atualizada!")
            return True
        except Exception as e:
            print(f"Erro ao injetar cookies: {e}")
            return False
    else:
        print("Arquivo de cookies não encontrado. Login manual necessário.")
        return False

def main():
    url = "https://freebitco.in"
    cookies_file = "cookies.json"

    # Caminho para o Chrome instalado
    chrome_executable_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    # Configuração do Chrome
    chrome_options = Options()
    chrome_options.binary_location = chrome_executable_path
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")  # Porta de depuração

    # Inicializa o WebDriver do Selenium
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        # Abre a URL especificada
        driver.get(url)

        # Injeta cookies
        if inject_cookies(driver, cookies_file, url):
            print("Login automático realizado com sucesso!")
        else:
            print("Não foi possível fazer login automático. Verifique os cookies.")
            driver.quit()
            return

        # Rolar até o elemento e clicar
        try:
            captcha_element = driver.find_element(By.CSS_SELECTOR, "#freeplay_form_cf_turnstile div")
            driver.execute_script("arguments[0].scrollIntoView();", captcha_element)
            captcha_element.click()
            print("Captcha resolvido!")

            # Após resolver o Captcha, tenta clicar no botão ROLL
            roll_button = driver.find_element(By.CSS_SELECTOR, "#free_play_form_button")
            roll_button.click()
            print("Botão ROLL clicado!")

        except Exception as e:
            print(f"Erro ao interagir com o site: {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
