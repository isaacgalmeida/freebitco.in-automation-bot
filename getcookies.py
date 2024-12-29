import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def main():
    # Configuração do Chrome
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-webgl")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--enable-unsafe-swiftshader")

    # Inicializar o WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        # Abrir o site
        url = "https://freebitco.in"
        print(f"*** Acesse o site: {url}")
        print("*** Por favor, faça login na mesma janela do navegador para gerar os cookies.")
        print("\033[91m*** Após concluir o login, digite 'salvar' no terminal e pressione Enter para salvar os cookies.\033[0m")

        driver.get(url)

        # Aguardar até que o usuário feche o navegador
        while True:
            if input("\033[91mDigite 'salvar' e pressione Enter após fazer login: \033[0m").strip().lower() == 'salvar':
                break

        # Obter os cookies
        cookies = driver.get_cookies()

        # Salvar os cookies em um arquivo JSON
        cookies_file = "cookies.json"
        with open(cookies_file, "w") as f:
            json.dump(cookies, f, indent=4)
        print(f"*** Cookies salvos com sucesso em '{cookies_file}'.")

    except Exception as e:
        print(f"Erro ao gerar os cookies: {e}")
    finally:
        # Fechar o navegador
        driver.quit()

    print("*** Agora você pode executar o software principal usando: python app.py")

if __name__ == "__main__":
    main()
