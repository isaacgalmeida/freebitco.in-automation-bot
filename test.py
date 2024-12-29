import os
import json
from seleniumbase import SB
from dotenv import load_dotenv

load_dotenv()

def save_screenshot(sb, filename):
    """
    Salva screenshots na pasta 'imgs/'.
    """
    screenshots_dir = "imgs"
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)  # Cria a pasta imgs/ se não existir
    sb.save_screenshot(os.path.join(screenshots_dir, filename))

def inject_cookies(sb, cookies_file, url):
    """
    Injeta cookies para login no site e atualiza a página.
    """
    sb.open(url)
    save_screenshot(sb, "01-open_page.jpg")

    if os.path.exists(cookies_file):
        try:
            # Carrega cookies do arquivo
            with open(cookies_file, "r") as f:
                cookies = json.load(f)

            # Injeta cada cookie no navegador
            for cookie in cookies:
                sb.driver.add_cookie(cookie)

            # Atualiza a página após injetar os cookies
            sb.refresh()
            print("Cookies injetados com sucesso e página atualizada!")
            save_screenshot(sb, "02-after_cookies.jpg")
            return True
        except Exception as e:
            print(f"Erro ao injetar cookies: {e}")
            save_screenshot(sb, "inject_cookies_error.jpg")
            return False
    else:
        print("Arquivo de cookies não encontrado. Login manual necessário.")
        return False

def handle_cloudflare_captcha(sb):
    """
    Resolve o Captcha Cloudflare usando CDP e o seletor do ID especificado.
    Rolamos até o elemento antes de clicar para garantir que esteja na tela.
    """
    try:
        print("Tentando resolver o Captcha usando CDP...")
        sb.activate_cdp_mode("https://freebitco.in")
        sb.sleep(2)  # Pausa para garantir que o Captcha foi carregado

        # Rolamos até o captcha para garantir que fique visível na janela
        sb.scroll_to("#freeplay_form_cf_turnstile div")
        sb.sleep(3)

        # Clique físico via PyAutoGUI (CDP)
        sb.cdp.gui_click_element("#freeplay_form_cf_turnstile div")
        print("Captcha clicado com sucesso!")
        save_screenshot(sb, "03-captcha_clicked.jpg")

        sb.sleep(10)  # Aguarda o processamento do Captcha
    except Exception as e:
        print(f"Erro ao resolver o Captcha: {e}")
        save_screenshot(sb, "03-captcha_error.jpg")
        return False
    return True

def main():
    url = "https://freebitco.in"
    cookies_file = "cookies.json"  # Certifique-se de que esse arquivo contém cookies válidos

    with SB(uc=True, test=True) as sb:
        # Define a posição e o tamanho da janela
        sb.driver.set_window_position(0, 0)
        sb.driver.set_window_size(1280, 720)

        # Injeta cookies e tenta fazer login automaticamente
        if inject_cookies(sb, cookies_file, url):
            print("Login automático realizado com sucesso!")
        else:
            print("Não foi possível fazer login automático. Verifique os cookies.")
            sb.quit()  # Encerra o navegador se não conseguir injetar os cookies
            return

        # Resolve o Captcha usando CDP
        if not handle_cloudflare_captcha(sb):
            print("Não foi possível resolver o Captcha. Encerrando.")
            return

        # Após resolver o Captcha, tenta clicar no botão ROLL
        try:
            sb.assert_element("#free_play_form_button", timeout=10)
            sb.click("#free_play_form_button")
            print("Botão ROLL clicado!")
            save_screenshot(sb, "04-roll_clicked.jpg")
        except Exception as e:
            print(f"Erro ao clicar no botão ROLL: {e}")
            save_screenshot(sb, "04-roll_error.jpg")

if __name__ == "__main__":
    main()
