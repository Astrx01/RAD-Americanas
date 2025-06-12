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
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Dados do email - configure aqui
EMAIL_REMETENTE = 'rastreadordepreco@gmail.com'
SENHA_REMETENTE = 'xgau omrq ezly zlur'
EMAIL_DESTINATARIO = 'destinatario@example.com'

def enviar_email_alerta(nome, url, preco_atual, precoDesejado, email_usuario):
    assunto = f"Alerta de preço: {nome}"
    corpo = f"""
    <p>O preço do produto <b>{nome}</b> caiu para <b>R${preco_atual:.2f}</b>.</p>
    <p>Seu preço desejado era: R${precoDesejado}</p>
    <p>Confira no link: <a href="{url}">{url}</a></p>
    """

    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = email_usuario  # envia para o email fornecido
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

# Cria a pasta do banco se não existir
os.makedirs('db', exist_ok=True)

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
def salvar_preco_em_db(nome, url, preco, precoDesejado, email):
    conn = sqlite3.connect('db/precos.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS precos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            url TEXT,
            preco REAL,
            precoDesejado REAL,
            email TEXT,
            data TEXT
        )
    ''')

    data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO precos (nome, url, preco, precoDesejado, email, data) VALUES (?, ?, ?, ?, ?, ?)',
                   (nome, url, preco, precoDesejado, email, data_atual))

    conn.commit()
    conn.close()
    print("✅ Preço salvo no banco de dados.")

# Função para plotar gráfico e salvar arquivo opcionalmente
def plotar_grafico_preco(nome, salvar_arquivo=False):
    conn = sqlite3.connect('db/precos.db')
    cursor = conn.cursor()

    cursor.execute("SELECT data, preco FROM precos WHERE nome = ? ORDER BY data", (nome,))
    resultados = cursor.fetchall()
    conn.close()

    if not resultados:
        print("Nenhum dado encontrado para plotar.")
        return None

    datas = []
    precos = []
    for data_str, preco in resultados:
        datas.append(datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S'))
        precos.append(preco)

    plt.figure(figsize=(12, 6))
    plt.plot(datas, precos, marker='o', linestyle='-', label=nome)
    plt.title(f"Histórico de Preços - {nome}")
    plt.xlabel("Data")
    plt.ylabel("Preço (R$)")
    plt.grid(True)
    plt.legend()

    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y %H:%M'))
    plt.xticks(rotation=45)
    plt.tight_layout()

    if salvar_arquivo:
        nome_arquivo = f"grafico_preco_{nome.replace(' ', '_')}.png"
        plt.savefig(nome_arquivo)
        print(f"Gráfico salvo em arquivo: {nome_arquivo}")
        return nome_arquivo
    else:
        plt.show()
        return None

# Execução principal
if __name__ == '__main__':
    url = input("Cole a URL do produto: ").strip()
    precoDesejado = input("Digite o preço desejado: ").strip()
    email = input("Digite seu Email para alerta de Preços: ").strip()

    try:
        nome, preco = get_info_americanas(url)
        if preco is not None:
            print(f"📦 Produto: {nome}")
            print(f"✅ Preço atual: R${preco:.2f}")
            print(f"🎯 Preço desejado: R${precoDesejado}")
            salvar_preco_em_db(nome, url, preco, precoDesejado, email)

            precoDesejado_float = float(precoDesejado.replace(',', '.'))
            if preco <= precoDesejado_float:
                enviar_email_alerta(nome, url, preco, precoDesejado, email)
                # Opcional: gerar gráfico e mostrar (ou salvar)
                plotar_grafico_preco(nome, salvar_arquivo=False)
            else:
                print("⏳ Preço ainda acima do desejado. Sem envio de alerta.")
        else:
            print("⚠️ Preço não encontrado.")
    except Exception as e:
        print(f"❌ Erro: {e}")
