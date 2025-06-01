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
def salvar_preco_em_db(nome, url, preco, nice,email):
    conn = sqlite3.connect('db/precos.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS precos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            url TEXT,
            preco REAL,
            nice TEXT,
            email TEXT,
            data TEXT
        )
    ''')

    data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO precos (nome, url, preco, nice, email, data) VALUES (?, ?, ?, ?, ?, ?)', (nome, url, preco, nice,email, data_atual))

    conn.commit()
    conn.close()
    print("✅ Preço salvo no banco de dados.")

# Execução principal
if __name__ == '__main__':
    url = input("Cole a URL do produto: ").strip()
    nice = input("Digite o preço desejado: ").strip()
    email= input("Digite seu Email para alerta de Preços:").strip()


    try:
        nome, preco = get_info_americanas(url)
        if preco is not None:
            print(f"📦 Produto: {nome}")
            print(f"✅ Preço atual: R${preco:.2f}")
            print(f"🎯 Preço desejado: R${nice}")
            salvar_preco_em_db(nome, url, preco, nice, email)
        else:
            print("⚠️ Preço não encontrado.")
    except Exception as e:
        print(f"Erro: {e}")

