import time
import logging
import os
import json
import requests
import platform
from dotenv import load_dotenv
from CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions

# Carrega as variáveis de ambiente
load_dotenv()

# Configura o logging
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
    Configura e retorna as opções do Chromium.
    """
    options = ChromiumOptions()
    options.set_paths(browser_path=browser_path)
    for argument in arguments:
        options.set_argument(argument)
    return options

def inject_cookies(driver, cookies_file, url):
    """
    Injeta os cookies na sessão do navegador usando o método set.cookies().
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
            logging.info("Cookies injetados com sucesso.")

            driver.get(url)
            logging.info("Página recarregada após aplicação dos cookies.")
            return True
        except Exception as e:
            logging.error(f"Erro ao injetar cookies: {e}")
            return False
    else:
        logging.warning("Arquivo de cookies não encontrado. Login manual necessário.")
        return False

def close_popups(driver):
    """
    Fecha quaisquer pop-ups ou banners na página.
    """
    try:
        popup = driver.ele('button:contains("NO THANKS")', timeout=3, show_errmsg=False)
        if popup:
            popup.click()
            logging.info("Popup fechado.")
    except Exception as e:
        logging.warning(f"Nenhum popup para fechar ou erro ao fechar popup: {e}")

def click_roll_button(driver):
    """
    Clica no botão 'Roll' após resolver o CAPTCHA.
    """
    try:
        roll_button = driver.ele('#free_play_form_button', timeout=10)
        if roll_button:
            roll_button.click()
            time.sleep(10)
            logging.info("Botão 'Roll' clicado.")
            return True
        else:
            logging.warning("Botão 'Roll' não encontrado.")
            return False
    except Exception as e:
        logging.error(f"Botão 'Roll' não encontrado ou não clicável: {e}")
        return False

def get_time_remaining(driver):
    """
    Recupera o tempo restante a partir da div 'time_remaining'.
    """
    try:
        time_remaining_div = driver.ele('#time_remaining', timeout=10)
        if time_remaining_div:
            time_remaining_text = time_remaining_div.text.replace('\n', ' ')
            logging.info(f"Texto bruto de time_remaining: {time_remaining_text}")
            
            if "Minutes" in time_remaining_text:
                minutes_part = time_remaining_text.split('Minutes')[0].strip()
                if minutes_part.isdigit():
                    minutes = int(minutes_part)
                    logging.info(f"Tempo restante extraído: {minutes} minutos.")
                    return minutes
                else:
                    logging.warning(f"Parte dos minutos não é um inteiro válido: {minutes_part}")
            else:
                logging.warning("Palavra 'Minutes' não encontrada no texto de time_remaining.")
        else:
            logging.warning("Div 'time_remaining' não encontrada.")
        return None
    except Exception as e:
        logging.error(f"Erro ao obter 'time_remaining': {e}")
        return None

def send_balance_to_telegram(driver):
    """
    Envia o saldo atual e o tempo restante para o Telegram.
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
            logging.info("Saldo e tempo restante enviados para o Telegram.")
    except Exception as e:
        logging.error(f"Erro ao enviar saldo para o Telegram: {e}")

def main():
    isHeadless = os.getenv('HEADLESS', 'false').lower() == 'true'
    
    # Inicia o display virtual apenas se o modo headless estiver ativo e o SO não for Windows
    display = None
    if isHeadless and platform.system() != 'Windows':
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
        "--remote-debugging-port=9222"
    ]

    # Se o modo headless estiver ativo, adiciona o argumento para execução sem interface gráfica.
    if isHeadless:
        arguments.append("--headless")

    options = get_chromium_options(browser_path, arguments)

    while True:
        browser_closed = False  # Flag para indicar se o browser já foi fechado nesta iteração
        try:
            driver = ChromiumPage(addr_or_opts=options)
            logging.info('Navegando para FreeBitco.in.')
            url = 'https://freebitco.in'
            driver.get(url)

            cookies_file = "cookies.json"
            if inject_cookies(driver, cookies_file, url):
                logging.info("Cookies aplicados. Login automático realizado com sucesso.")
            else:
                logging.warning("Cookies não puderam ser aplicados. Verifique o arquivo cookies.json.")

            # Fecha pop-ups, se houver
            close_popups(driver)

            # Verifica se a div 'time_remaining' já existe (indica que o roll já foi feito)
            time_remaining = get_time_remaining(driver)
            if time_remaining is not None:
                wait_time = (time_remaining + 1) * 60
                logging.info(f"Roll já efetuado. Aguardando {time_remaining + 1} minutos antes de tentar novamente.")
                driver.quit()
                browser_closed = True
                time.sleep(wait_time)
                continue

            # Resolve o CAPTCHA e clica no botão 'Roll'
            cf_bypasser = CloudflareBypasser(driver)
            cf_bypasser.click_verification_button()

            logging.info("Aguardando 10 segundos antes de clicar no botão 'Roll'.")
            time.sleep(10)

            if click_roll_button(driver):
                time_remaining = get_time_remaining(driver)
                if time_remaining is not None:
                    send_balance_to_telegram(driver)
                    wait_time = (time_remaining + 1) * 60
                    logging.info("Roll efetuado com sucesso. Fechando o browser e aguardando para reabrir...")
                    driver.quit()
                    browser_closed = True
                    logging.info(f"Aguardando {time_remaining + 1} minutos antes de tentar novamente.")
                    time.sleep(wait_time)
                    continue
                else:
                    logging.warning("Roll não completado com sucesso. Tentando novamente...")
            else:
                logging.warning("Não foi possível clicar no botão 'Roll'. Tentando novamente...")
        except Exception as e:
            logging.error("Ocorreu um erro: %s. Reiniciando o browser...", str(e))
            time.sleep(5)  # Aguarda antes de reiniciar
        finally:
            try:
                if not browser_closed:
                    logging.info('Fechando o browser.')
                    driver.quit()
                if display:
                    display.stop()
            except Exception as cleanup_error:
                logging.error(f"Erro durante a limpeza do browser: {cleanup_error}")

if __name__ == '__main__':
    main()
