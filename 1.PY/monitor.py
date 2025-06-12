import schedule
import time

def tarefa():
    url = "SUA_URL_AQUI"  # Defina a URL que deseja monitorar
    nome, preco = get_info_americanas(url)
    if preco is not None:
        print(f"📦 Produto: {nome}")
        print(f"✅ Preço atual: R${preco:.2f}")
        salvar_preco_em_db(nome, url, preco)
    else:
        print("⚠️ Preço não encontrado.")

# Agenda a tarefa para rodar a cada 6 horas
schedule.every(6).hours.do(tarefa)

print("⏰ Monitoramento iniciado. Executando a cada 6 horas.")
tarefa()  # Executa imediatamente na primeira vez

while True:
    schedule.run_pending()
    time.sleep(60)
