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

# Carrega as variáveis de ambiente
load_dotenv()

def sleep_until(seconds):
    target = time.time() + seconds
    while time.time() < target:
        time.sleep(1)  # dorme em intervalos curtos

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

    # Ajuste no user-agent para evitar aspas dentro de aspas
    options.set_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/134.0.0.0 Safari/537.36')
    options.set_argument('--disable-blink-features=AutomationControlled')
    options.set_argument('--disable-infobars')

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
        # Remova o show_errmsg=False, pois não é suportado na versão 4.1.0.17
        popup = driver.ele('button:contains("NO THANKS")', timeout=3)
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
        
        index_minutes = time_remaining.find("Minutes")
        if index_minutes != -1:
            end_index = index_minutes + len("Minutes")
            # Verifica se existe um caractere após "Minutes" e se ele não é um espaço
            if end_index < len(time_remaining) and time_remaining[end_index] != " ":
                time_remaining = time_remaining[:end_index] + " " + time_remaining[end_index:]
        
        telegram_token = os.getenv("TELEGRAM_TOKEN")
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if telegram_token and telegram_chat_id:
            message = f"BTC Balance: {balance}\nTime Remaining: {time_remaining}"
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            requests.post(url, data={"chat_id": telegram_chat_id, "text": message})
            logging.info("Saldo e tempo restante enviados para o Telegram.")
    except Exception as e:
        logging.error(f"Erro ao enviar saldo para o Telegram: {e}")

def minimize_window_windows():
    """
    Utiliza pywin32 para minimizar a janela do navegador no Windows.
    Caso não queira instalar pywin32, comente ou remova esta função.
    """
    try:
        import win32gui
        import win32con

        time.sleep(1)

        def enumHandler(hwnd, lParam):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                # Ajuste a verificação conforme o título do seu navegador (Ex.: "Chrome", "Brave", etc.)
                if "Brave" in title:
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                    logging.info(f"Janela '{title}' minimizada via win32gui.")

        win32gui.EnumWindows(enumHandler, None)
    except Exception as e:
        logging.error(f"Erro ao minimizar a janela com win32gui: {e}")

def check_internal_server_error(driver):
    """
    Verifica se a página carregada contém o erro 500 Internal Server Error.
    Tenta obter o HTML via driver.html; se isso falhar, utiliza execute_script.
    """
    try:
        time.sleep(5)  # aguarda alguns segundos para a página carregar
        try:
            # Tenta obter o HTML pelo método padrão do DrissionPage
            page_source = driver.html
        except Exception as e:
            logging.error(f"driver.html falhou: {e}. Tentando com execute_script...")
            page_source = driver.driver.execute_script("return document.documentElement.outerHTML")
        
        #logging.info(f"HTML retornado:\n{page_source}")
        
        if "Internal Server Error" in page_source or "500 Internal Server Error" in page_source:
            return True
    except Exception as e:
        logging.error(f"Erro ao verificar status da página: {e}")
    return False


def main():
    isHeadless = os.getenv('HEADLESS', 'false').lower() == 'true'
    
    # Se estiver em headless e não for Windows, inicia o display virtual
    display = None
    if isHeadless and platform.system() != 'Windows':
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(1920, 1080))
        display.start()

    # Obtém o caminho definido na variável de ambiente
    browser_path = os.getenv('CHROME_PATH')
    if not browser_path or not os.path.exists(browser_path):
        logging.warning("CHROME_PATH não definido ou inválido. Utilizando o Chrome padrão do sistema.")
        if platform.system() == "Windows":
            browser_path = "chrome"
        elif platform.system() == "Darwin":
            browser_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        else:
            browser_path = "/usr/bin/google-chrome"

    base_arguments = [
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

    if isHeadless:
        base_arguments.append("--headless")
    else:
        # Inicia a janela minimizada
        base_arguments.append("--start-minimized")

    while True:
        # Cria um diretório de perfil temporário para forçar uma nova instância
        user_data_dir = tempfile.mkdtemp(prefix="drission_profile_")
        arguments = base_arguments.copy()
        arguments.append(f"--user-data-dir={user_data_dir}")
        
        options = get_chromium_options(browser_path, arguments)
        browser_closed = False
        
        try:
            driver = ChromiumPage(addr_or_opts=options)
            
            # Minimize a janela (somente Windows e não headless).
            # Se não quiser instalar pywin32, comente a linha abaixo.
            if platform.system() == "Windows" and not isHeadless:
                minimize_window_windows()

            logging.info('Navegando para FreeBitco.in.')
            url = 'https://freebitco.in'
            driver.get(url)

            cookies_file = "cookies.json"
            if inject_cookies(driver, cookies_file, url):
                logging.info("Cookies aplicados. Login automático realizado com sucesso.")
            else:
                logging.warning("Cookies não puderam ser aplicados. Verifique o arquivo cookies.json.")

            close_popups(driver)

                        # Verifica se a página retornou erro 500
            if check_internal_server_error(driver):
                logging.error("Erro 500 Internal Server Error detectado. Fechando o browser e aguardando 10 minutos.")
                driver.quit()
                sleep_until(600)  # aguarda 600 segundos (10 minutos)
                continue

            time_remaining = get_time_remaining(driver)
            if time_remaining is not None:
                wait_time = (time_remaining + 1) * 60
                logging.info(f"Roll já efetuado. Aguardando {time_remaining + 1} minutos antes de tentar novamente.")
                driver.quit()
                browser_closed = True
                sleep_until(wait_time)
                continue

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
                    sleep_until(wait_time)
                    continue
                else:
                    logging.warning("Roll não completado com sucesso. Tentando novamente...")
            else:
                logging.warning("Não foi possível clicar no botão 'Roll'. Tentando novamente...")

        except Exception as e:
            logging.error("Ocorreu um erro: %s. Reiniciando o browser...", str(e))
            time.sleep(5)

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
