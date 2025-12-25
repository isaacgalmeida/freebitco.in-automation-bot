import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def main():
    print("🍪 Headless Cookie Generator")
    print("⚠️  IMPORTANTE: Você precisará fazer login manualmente via VNC ou usar cookies de outra máquina")
    
    # Configuração do Chrome headless
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Novo modo headless
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    
    # Para debug - salva screenshots
    chrome_options.add_argument("--enable-logging")
    chrome_options.add_argument("--log-level=0")

    try:
        # Inicializar o WebDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        # Abrir o site
        url = "https://freebitco.in"
        print(f"📱 Acessando: {url}")
        driver.get(url)
        
        # Salvar screenshot para debug
        driver.save_screenshot("freebitcoin_page.png")
        print("📸 Screenshot salva como 'freebitcoin_page.png'")
        
        print("⚠️  ATENÇÃO: Este é um modo headless!")
        print("⚠️  Você não pode fazer login interativo aqui.")
        print("⚠️  Use uma das outras opções:")
        print("   1. Gere cookies em uma máquina com GUI")
        print("   2. Use o Docker com VNC (docker-compose.cookies.yml)")
        
        # Para demonstração, vamos apenas pegar os cookies atuais (vazios)
        cookies = driver.get_cookies()
        
        if cookies:
            with open("cookies_empty.json", "w") as f:
                json.dump(cookies, f, indent=4)
            print("📁 Cookies vazios salvos em 'cookies_empty.json' (apenas para teste)")
        
        print("\n🔧 Para gerar cookies reais, use:")
        print("   docker compose -f docker-compose.cookies.yml up -d")
        print("   Depois acesse: http://seu-ip:7900 (senha: cookies123)")

    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    main()