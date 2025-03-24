# FreeBitco.in Automation Bot

Este é um projeto para automatizar a interação com o site [FreeBitco.in](https://freebitco.in), incluindo a realização automática do login e o clique no botão "Roll". Além disso, o bot notifica o saldo e o tempo restante para o próximo clique via Telegram.

---

## Requisitos

- **Python 3.8+**
- **Google Chrome** instalado no sistema.
- **Pacotes Python** listados em `requirements.txt`.

---

## Configuração

### 1. **Instalar Dependências**

Antes de tudo, instale as dependências do projeto usando o `pip`:

```bash
pip install -r requirements.txt
```

---

### 2. **Gerar Cookies com `getcookies.py`**

1. Execute o script `getcookies.py`:

   ```bash
   python getcookies.py
   ```

2. Será aberta uma janela do navegador. Acesse o site [FreeBitco.in](https://freebitco.in) e faça login manualmente.
3. Após concluir o login, volte ao terminal e digite `salvar` para capturar os cookies.
4. Verifique se o arquivo `cookies.json` foi gerado na pasta do projeto.

---

### 3. **Configurar Variáveis de Ambiente**

Crie um arquivo `.env` na raiz do projeto e adicione as seguintes variáveis:

```env
TELEGRAM_TOKEN=seu_bot_token
TELEGRAM_CHAT_ID=seu_chat_id
HEADLESS=false
CHROME_PATH=/caminho/para/google-chrome
```

- **`TELEGRAM_TOKEN`**: O token do seu bot no Telegram.
- **`TELEGRAM_CHAT_ID`**: O ID do chat onde as mensagens serão enviadas.
- **`HEADLESS`**: Define se o navegador será executado em modo headless (sem interface gráfica). Use `true` para headless ou `false` para com interface gráfica.
- **`CHROME_PATH`**: Caminho para o executável do Google Chrome.

---

### 4. **Executar o Bot**

Execute o script principal `app_windows.py`:

```bash
python app_windows.py
```

---

## Funcionamento

1. O bot utiliza os cookies gerados para fazer login automático no site.
2. Fecha popups e banners automaticamente antes de interagir com o site.
3. Clica no botão "Roll" e, caso haja um tempo restante (`time_remaining`), aguarda o tempo especificado antes de tentar novamente.
4. Notifica o saldo atual e o tempo restante via Telegram após cada clique.

---

## Logs

Os logs das execuções são salvos no arquivo `cloudflare_bypass.log`, na raiz do projeto.

---

## Solução de Problemas

1. **Erro ao executar `getcookies.py`**:

   - Certifique-se de que o Google Chrome está instalado e configurado corretamente.
   - Verifique se o caminho para o Chrome no `.env` (`CHROME_PATH`) está correto.

2. **Não consegue clicar no botão "Roll"**:

   - Verifique se há popups ou banners bloqueando o botão. O script tenta fechar automaticamente, mas revise a função `close_popups`.

3. **Mensagens de erro ao enviar para o Telegram**:
   - Certifique-se de que as variáveis `TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID` estão configuradas corretamente no arquivo `.env`.

---

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar PRs com melhorias ou correções.

---

## Licença

Este projeto está sob a licença MIT. Consulte o arquivo `LICENSE` para mais detalhes.
