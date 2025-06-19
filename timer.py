import schedule
import time
import sqlite3
from rastreador import get_info_americanas, salvar_preco_em_db, enviar_email_alerta
from datetime import datetime

def verificar_precos():
    print(f"\nVerificação iniciada: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    conn = sqlite3.connect('db/precos.db')
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT nome, url, precoDesejado, email FROM precos")
    produtos = cursor.fetchall()
    conn.close()

    for nome, url, precoDesejado, email in produtos:
        try:
            nome_atual, preco_atual = get_info_americanas(url)
            if preco_atual is None:
                print(f"Não foi possível obter o preço para: {nome}")
                continue

            print(f"Produto: {nome}")
            print(f"Preço atual: R${preco_atual:.2f} | Desejado: R${precoDesejado}")

            salvar_preco_em_db(nome_atual, url, preco_atual, precoDesejado, email)

            precoDesejado_float = float(str(precoDesejado).replace(',', '.'))
            if preco_atual <= precoDesejado_float:
                enviar_email_alerta(nome_atual, url, preco_atual, precoDesejado, email)
            else:
                print("Sem alerta: preço ainda acima do desejado.")

        except Exception as e:
            print(f"Erro ao verificar {nome}: {e}")

schedule.every(5).minutes.do(verificar_precos)

print("Iniciando o monitoramento a cada 6 horas...")

verificar_precos()

while True:
    schedule.run_pending()
    time.sleep(60)