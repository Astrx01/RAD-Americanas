import sqlite3
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Dados do email - configure aqui
EMAIL_REMETENTE = 'seuemail@gmail.com'
SENHA_REMETENTE = 'sua_senha_de_app_aqui'
EMAIL_DESTINATARIO = 'destinatario@example.com'

def enviar_email_alerta(nome, url, preco_atual, preco_desejado):
    assunto = f"Alerta de preço: {nome}"
    corpo = f"""
    <p>O preço do produto <b>{nome}</b> caiu para <b>R${preco_atual:.2f}</b>.</p>
    <p>Seu preço desejado era: R${preco_desejado}</p>
    <p>Confira no link: <a href="{url}">{url}</a></p>
    """

    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'html'))

    try:
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(EMAIL_REMETENTE, SENHA_REMETENTE)
        servidor.send_message(msg)
        servidor.quit()
        print("✅ Email de alerta enviado!")
    except Exception as e:
        print(f"❌ Falha ao enviar email: {e}")

# Função para extrair o nome e o preço do produto
def get_info_americanas(url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 15)

        try:
            nome_element = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            nome = nome_element.text.strip()
        except TimeoutException:
            nome = "Nome não encontrado"

        try:
            price_element = wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "R$")]')))
            price = price_element.text
            price = price.replace("R$", "").replace(".", "").replace(",", ".").strip()
            preco = float(price)
        except TimeoutException:
            print("❌ Timeout: o seletor do preço não foi encontrado.")
            return nome, None

        return nome, preco

    except Exception as e:
        print(f"Erro inesperado: {e}")
        return None, None
    finally:
        driver.quit()

# Função para salvar no SQLite
def salvar_preco_em_db(nome, url, preco, nice):
    conn = sqlite3.connect('db/precos.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS precos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            url TEXT,
            preco REAL,
            nice TEXT,
            data TEXT
        )
    ''')

    data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO precos (nome, url, preco, nice, data) VALUES (?, ?, ?, ?, ?)', (nome, url, preco, nice, data_atual))

    conn.commit()
    conn.close()
    print("✅ Preço salvo no banco de dados.")

# Execução principal
if __name__ == '__main__':
    url = input("Cole a URL do produto: ").strip()
    nice = input("Digite o preço desejado: ").strip()

    try:
        nome, preco = get_info_americanas(url)
        if preco is not None:
            print(f"📦 Produto: {nome}")
            print(f"✅ Preço atual: R${preco:.2f}")
            salvar_preco_em_db(nome, url, preco, nice)

            # Verifica se o preço atual é menor ou igual ao desejado
            preco_desejado = float(nice.replace(',', '.'))
            if preco <= preco_desejado:
                enviar_email_alerta(nome, url, preco, preco_desejado)
            else:
                print("Preço ainda acima do desejado. Sem envio de alerta.")
        else:
            print("⚠️ Preço não encontrado.")
    except Exception as e:
        print(f"Erro: {e}")
