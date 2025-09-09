import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import datetime

# --- Configuração de Persistência ---
# Define o diretório onde o arquivo do contador será armazenado.
# Certifique-se de que este caminho corresponde ao "mount path" do seu volume persistente no Coolify.
PERSISTENT_DATA_PATH = "/app/data"
RUN_COUNT_FILE = os.path.join(PERSISTENT_DATA_PATH, "run_count.txt")
# --- Fim da Configuração de Persistência ---

# Carrega variáveis do .env
load_dotenv()

URL_LOGIN = "https://uservoz.uservoz.com.br/painel/"
USERNAME = os.environ.get("SERVICE_USERNAME")
PASSWORD = os.environ.get("SERVICE_PASSWORD")
WEBHOOK_URL = os.environ.get("GOOGLE_CHAT_WEBHOOK_URL")
GERENTE_WEBHOOK = os.environ.get("GOOGLE_CHAT_WEBHOOK_GERENTE")
LOGO_URL = os.environ.get("GOOGLE_CHAT_LOGO_URL")

def get_run_count():
    """Lê o contador do arquivo persistente."""
    try:
        if not os.path.exists(PERSISTENT_DATA_PATH):
            os.makedirs(PERSISTENT_DATA_PATH)
        with open(RUN_COUNT_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def set_run_count(count):
    """Salva o novo valor do contador no arquivo persistente."""
    with open(RUN_COUNT_FILE, "w") as f:
        f.write(str(count))

def send_notification(message_text, saldo_info, webhook_url, run_count):
    try:
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        
        chat_message_header = f"(Execução #{run_count})\n\n"
        
        payload = {
            "cardsV2": [
                {
                    "cardId": "saldo-notification-card",
                    "card": {
                        "header": {"title": "📢 Monitoramento de Saldo VOIP", "subtitle": "Inovação Informa"},
                        "sections": [
                            {
                                "header": chat_message_header + "📊 Status Atual",
                                "collapsible": False,
                                "widgets": [
                                    {"image": {"imageUrl": LOGO_URL, "altText": "Logo da Inovação"}},
                                    {"decoratedText": {"topLabel": "💰 Saldo", "text": f"<b>{saldo_info}</b>", "wrapText": True}},
                                    {"decoratedText": {"topLabel": "ℹ️ Mensagem", "text": message_text, "wrapText": True}}
                                ],
                            },
                            {
                                "header": "⚡ Ações Rápidas",
                                "widgets": [
                                    {"buttonList": {"buttons": [
                                        {"text": "Abrir Painel", "onClick": {"openLink": {"url": URL_LOGIN}}},
                                        {"text": "Ver Detalhes", "onClick": {"openLink": {"url": "https://statuspage.io/"}}}
                                    ]}},
                                    {"textParagraph": {"text": "<font color=\"#808080\">Enviado pelo setor de Inovação 💡</font>"}}
                                ]
                            }
                        ]
                    }
                }
            ]
        }
        response = requests.post(webhook_url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Notificação enviada com sucesso para {webhook_url}.")
    except Exception as e:
        print(f"Erro ao enviar notificação: {e}")

def job(run_count):
    print(f"[{datetime.datetime.now()}] Iniciando tarefa #{run_count}...")
    driver = None
    
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        driver.get(URL_LOGIN)
        time.sleep(3)
        
        driver.find_element(By.XPATH, '//*[@id="login"]').send_keys(USERNAME)
        driver.find_element(By.XPATH, '//*[@id="senha"]').send_keys(PASSWORD)
        driver.find_element(By.XPATH, '//*[@id="bt-login"]/input').click()
        time.sleep(5)
        saldo_element = driver.find_element(By.XPATH, '//*[@id="index_boxs"]/div[1]/table/tbody/tr[5]/td[2]')
        saldo_text = saldo_element.text
        saldo_float = float(saldo_text.replace("R$", "").replace(",", ".").strip())
        saldo_formatado = f"R$ {saldo_float:.2f}"

        if saldo_float < 100:
            message = f"🚨 Atenção: Saldo crítico! {saldo_formatado}. Contactar o setor responsável, estamos sem créditos."
            send_notification(message, saldo_formatado, GERENTE_WEBHOOK, run_count)
            send_notification(message, saldo_formatado, WEBHOOK_URL, run_count)
        elif saldo_float < 200:
            message = f"🚨 Atenção: Saldo abaixo do limite. {saldo_formatado}."
            send_notification(message, saldo_formatado, WEBHOOK_URL, run_count)
        else:
            message = f"👍 Saldo suficiente. {saldo_formatado}."
            send_notification(message, saldo_formatado, WEBHOOK_URL, run_count)

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        send_notification("🚨 **ERRO CRÍTICO NO SCRIPT!** 🚨", f"O script falhou com o erro: {e}. Verifique os logs do Coolify.", WEBHOOK_URL, run_count)
    finally:
        if driver:
            driver.quit()
            print("WebDriver encerrado.")

if __name__ == "__main__":
    while True:
        run_count = get_run_count() + 1
        set_run_count(run_count)
        job(run_count)
        print(f"Execução #{run_count} concluída. Esperando 5 minutos para a próxima...")
        time.sleep(10000) # 604.800 segundos = 7 dias 