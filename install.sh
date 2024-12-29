# Atualize os pacotes
sudo apt update && sudo apt upgrade -y

# Instale dependências do Chrome/Chromium
sudo apt install -y wget unzip xvfb libxi6 libgconf-2-4 libappindicator3-1 fonts-liberation

# Instale o Google Chrome (Stable)
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt --fix-broken install -y

# Instale o Python 3 e pip
sudo apt install -y python3 python3-pip

# Instale bibliotecas Python necessárias
pip3 install -r requirements.txt
