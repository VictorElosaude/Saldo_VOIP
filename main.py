import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
import datetime

# Carrega variáveis do .env
load_dotenv()

URL_LOGIN = "https://uservoz.uservoz.com.br/painel/"
USERNAME = os.environ.get("SERVICE_USERNAME")
PASSWORD = os.environ.get("SERVICE_PASSWORD")
WEBHOOK_URL = os.environ.get("GOOGLE_CHAT_WEBHOOK_URL")
GERENTE_WEBHOOK = os.environ.get("GOOGLE_CHAT_WEBHOOK_GERENTE")
LOGO_URL = os.environ.get("GOOGLE_CHAT_LOGO_URL")

def send_notification(message_text, saldo_info, webhook_url=WEBHOOK_URL):
    try:
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        payload = {
            "cardsV2": [
                {
                    "cardId": "saldo-notification-card",
                    "card": {
                        "header": {"title": "📢 Monitoramento de Saldo VOIP", "subtitle": "Inovação Informa"},
                        "sections": [
                            {
                                "header": "📊 Status Atual",
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

def job():
    print(f"[{datetime.datetime.now()}] Iniciando tarefa agendada...")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
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
            send_notification(message, saldo_formatado, GERENTE_WEBHOOK)
            send_notification(message, saldo_formatado, WEBHOOK_URL)
        elif saldo_float < 200:
            message = f"🚨 Atenção: Saldo abaixo do limite. {saldo_formatado}."
            send_notification(message, saldo_formatado)
        else:
            message = f"👍 Saldo suficiente. {saldo_formatado}."
            send_notification(message, saldo_formatado)
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    # Executa toda segunda-feira às 09:00
    scheduler.add_job(job, 'cron', day_of_week='mon', hour=13, minute=15)
    print("Agendamento iniciado. Esperando a próxima execução...")
    scheduler.start()
