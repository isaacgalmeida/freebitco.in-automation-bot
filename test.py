import os
import json
from dotenv import load_dotenv
from CloudflareBypasser import CloudflareBypasser
from DrissionPage import ChromiumPage

load_dotenv()

def inject_cookies(driver, cookies_file):
    """
    Injeta cookies para login no site.
    """
    if os.path.exists(cookies_file):
        try:
            with open(cookies_file, "r") as f:
                cookies = json.load(f)

            for cookie in cookies:
                driver.add_cookies(cookie)

            driver.reload()
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

    # Inicializa o ChromiumPage
    driver = ChromiumPage()

    try:
        # Abre a URL especificada
        driver.get(url)

        # Usa o CloudflareBypasser para contornar proteção do site
        cf_bypasser = CloudflareBypasser(driver)
        if cf_bypasser.bypass():
            print("Proteção Cloudflare contornada com sucesso!")
        else:
            print("Falha ao contornar a proteção do Cloudflare.")
            driver.close_driver()
            return

        # Injeta cookies
        if inject_cookies(driver, cookies_file):
            print("Login automático realizado com sucesso!")
        else:
            print("Não foi possível fazer login automático. Verifique os cookies.")
            driver.close_driver()
            return

        # Rolar até o elemento e clicar
        try:
            captcha_element = driver.ele('#freeplay_form_cf_turnstile div')
            if captcha_element:
                driver.run_js("arguments[0].scrollIntoView();", captcha_element)
                captcha_element.click()
                print("Captcha resolvido!")

                # Após resolver o Captcha, tenta clicar no botão ROLL
                roll_button = driver.ele("#free_play_form_button")
                if roll_button:
                    roll_button.click()
                    print("Botão ROLL clicado!")
                else:
                    print("Botão ROLL não encontrado.")
            else:
                print("Captcha não encontrado.")
        except Exception as e:
            print(f"Erro ao interagir com o site: {e}")

    finally:
        driver.close_driver()

if __name__ == "__main__":
    main()
