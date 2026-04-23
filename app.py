from datetime import datetime
import time
import logging
import os
import json
import requests
import platform
import tempfile
import shutil
from dotenv import load_dotenv
from CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage, ChromiumOptions

# Carrega as variáveis de ambiente
load_dotenv()

def sleep_until(seconds):
    target = time.time() + seconds
    while time.time() < target:
        time.sleep(1)

# Configura o logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cloudflare_bypass.log', mode='w')
    ]
)

def safe_quit(driver):
    """Fecha o driver de forma segura, ignorando erros internos do DrissionPage."""
    if driver is None:
        return
    try:
        driver.quit()
    except Exception as e:
        logging.warning(f"Ignorando erro ao encerrar driver: {e}")
    # Tenta matar processos chrome órfãos em caso de falha
    try:
        if platform.system() != "Windows":
            os.system("pkill -f 'chrome.*--remote-debugging-port=9222' >/dev/null 2>&1")
    except Exception:
        pass

def get_chromium_options(browser_path: str, arguments: list) -> ChromiumOptions:
    options = ChromiumOptions()
    options.set_paths(browser_path=browser_path)
    for argument in arguments:
        options.set_argument(argument)

    options.set_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/134.0.0.0 Safari/537.36')
    options.set_argument('--disable-blink-features=AutomationControlled')
    options.set_argument('--disable-infobars')
    return options

def inject_cookies(driver, cookies_file, url):
    if os.path.exists(cookies_file):
        try:
            with open(cookies_file, "r") as f:
                cookies = json.load(f)

            formatted_cookies = [
                f"name={c['name']}; value={c['value']}; domain={c['domain']}; path={c['path']};"
                for c in cookies
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
    try:
        popup = driver.ele('button:contains("NO THANKS")', timeout=3)
        if popup:
            popup.click()
            logging.info("Popup fechado.")
    except Exception as e:
        logging.warning(f"Nenhum popup para fechar ou erro ao fechar popup: {e}")

def click_roll_button(driver):
    try:
        roll_button = driver.ele('#free_play_form_button', timeout=10)
        if roll_button:
            roll_button.click()
            time.sleep(10)
            logging.info("Botão 'Roll' clicado.")
            return True
        logging.warning("Botão 'Roll' não encontrado.")
        return False
    except Exception as e:
        logging.error(f"Botão 'Roll' não encontrado ou não clicável: {e}")
        return False

def get_time_remaining(driver):
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
                logging.warning(f"Parte dos minutos não é um inteiro válido: {minutes_part}")
            else:
                logging.warning("Palavra 'Minutes' não encontrada no texto de time_remaining.")
        else:
            logging.warning("Div 'time_remaining' não encontrada.")
        return None
    except Exception as e:
        logging.error(f"Erro ao obter 'time_remaining': {e}")
        return None

TELEGRAM_STATE_FILE = "telegram_last_send.json"

def _today_str():
    return datetime.now().strftime("%Y-%m-%d")

def _already_sent_today(state_file: str = TELEGRAM_STATE_FILE) -> bool:
    try:
        if not os.path.exists(state_file):
            return False
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("last_sent_date") == _today_str()
    except Exception as e:
        logging.warning(f"Falha ao ler estado de envio do Telegram: {e}")
        return False

def _mark_sent_today(state_file: str = TELEGRAM_STATE_FILE):
    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({"last_sent_date": _today_str()}, f)
    except Exception as e:
        logging.warning(f"Falha ao salvar estado de envio do Telegram: {e}")

def send_balance_to_telegram(driver):
    if _already_sent_today():
        logging.info("Mensagem do Telegram já foi enviada hoje. Pulando envio.")
        return
    try:
        balance = driver.ele("#balance", timeout=10).text
        time_remaining = driver.ele("#time_remaining", timeout=10).text.replace('\n', ' ')

        idx = time_remaining.find("Minutes")
        if idx != -1:
            end = idx + len("Minutes")
            if end < len(time_remaining) and time_remaining[end] != " ":
                time_remaining = time_remaining[:end] + " " + time_remaining[end:]

        telegram_token = os.getenv("TELEGRAM_TOKEN")
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if telegram_token and telegram_chat_id:
            message = f"BTC Balance: {balance}\nTime Remaining: {time_remaining}"
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            resp = requests.post(url, data={"chat_id": telegram_chat_id, "text": message}, timeout=20)
            if resp.status_code == 200:
                logging.info("Saldo e tempo restante enviados para o Telegram (1x por dia).")
                _mark_sent_today()
            else:
                logging.error(f"Falha ao enviar Telegram: HTTP {resp.status_code} - {resp.text}")
        else:
            logging.warning("TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID não configurados.")
    except Exception as e:
        logging.error(f"Erro ao enviar saldo para o Telegram: {e}")

def minimize_window_windows():
    try:
        import win32gui
        import win32con
        time.sleep(1)

        def enumHandler(hwnd, lParam):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "Brave" in title or "Chrome" in title:
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                    logging.info(f"Janela '{title}' minimizada via win32gui.")

        win32gui.EnumWindows(enumHandler, None)
    except Exception as e:
        logging.error(f"Erro ao minimizar a janela com win32gui: {e}")

def check_internal_server_error(driver):
    try:
        time.sleep(5)
        try:
            page_source = driver.html
        except Exception as e:
            logging.error(f"driver.html falhou: {e}. Tentando com execute_script...")
            page_source = driver.driver.execute_script("return document.documentElement.outerHTML")
        if "Internal Server Error" in page_source or "500 Internal Server Error" in page_source:
            return True
    except Exception as e:
        logging.error(f"Erro ao verificar status da página: {e}")
    return False


def main():
    isHeadless = os.getenv('HEADLESS', 'false').lower() == 'true'

    display = None
    if isHeadless and platform.system() != 'Windows':
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(1920, 1080))
        display.start()

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
        base_arguments.append("--headless=new")
    else:
        base_arguments.append("--start-minimized")

    consecutive_failures = 0

    while True:
        # IMPORTANTE: inicializar driver e user_data_dir ANTES do try
        driver = None
        user_data_dir = None
        browser_closed = False

        try:
            user_data_dir = tempfile.mkdtemp(prefix="drission_profile_")
            arguments = base_arguments.copy()
            arguments.append(f"--user-data-dir={user_data_dir}")

            options = get_chromium_options(browser_path, arguments)
            driver = ChromiumPage(addr_or_opts=options)

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

            if check_internal_server_error(driver):
                logging.error("Erro 500 Internal Server Error detectado. Fechando o browser e aguardando 10 minutos.")
                safe_quit(driver)
                driver = None
                browser_closed = True
                sleep_until(600)
                continue

            time_remaining = get_time_remaining(driver)
            if time_remaining is not None:
                wait_time = (time_remaining + 1) * 60
                logging.info(f"Roll já efetuado. Aguardando {time_remaining + 1} minutos antes de tentar novamente.")
                safe_quit(driver)
                driver = None
                browser_closed = True
                sleep_until(wait_time)
                continue

            try:
                cf_bypasser = CloudflareBypasser(driver)
                cf_bypasser.click_verification_button()
            except Exception as e:
                logging.warning(f"Falha no CloudflareBypasser: {e}. Continuando mesmo assim...")

            logging.info("Aguardando 10 segundos antes de clicar no botão 'Roll'.")
            time.sleep(10)

            if click_roll_button(driver):
                time_remaining = get_time_remaining(driver)
                if time_remaining is not None:
                    # Envia Telegram ANTES de fechar o driver
                    try:
                        send_balance_to_telegram(driver)
                    except Exception as e:
                        logging.error(f"Erro ao enviar ao Telegram (ignorado): {e}")

                    wait_time = (time_remaining + 1) * 60
                    logging.info("Roll efetuado com sucesso. Fechando o browser e aguardando para reabrir...")
                    safe_quit(driver)
                    driver = None
                    browser_closed = True
                    consecutive_failures = 0
                    logging.info(f"Aguardando {time_remaining + 1} minutos antes de tentar novamente.")
                    sleep_until(wait_time)
                    continue
                else:
                    logging.warning("Roll não completado com sucesso. Tentando novamente...")
            else:
                logging.warning("Não foi possível clicar no botão 'Roll'. Tentando novamente...")

            consecutive_failures += 1

        except Exception as e:
            consecutive_failures += 1
            logging.error("Ocorreu um erro: %s. Reiniciando o browser...", str(e))
            time.sleep(5)

        finally:
            # Limpeza segura — driver sempre existe como variável (None ou não)
            if not browser_closed:
                try:
                    logging.info('Fechando o browser.')
                    safe_quit(driver)
                except Exception as cleanup_error:
                    logging.error(f"Erro durante a limpeza do browser: {cleanup_error}")

            # Remove profile temporário
            if user_data_dir and os.path.exists(user_data_dir):
                try:
                    shutil.rmtree(user_data_dir, ignore_errors=True)
                except Exception:
                    pass

        # Backoff exponencial se estiver falhando repetidamente
        if consecutive_failures >= 5:
            backoff = min(300, 30 * consecutive_failures)
            logging.warning(f"{consecutive_failures} falhas consecutivas. Aguardando {backoff}s antes de tentar de novo.")
            sleep_until(backoff)

    if display:
        try:
            display.stop()
        except Exception:
            pass


if __name__ == '__main__':
    main()