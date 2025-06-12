import sqlite3

# Caminho para o banco de dados
caminho_banco = 'db/precos.db'

# Conecta ao banco
conn = sqlite3.connect(caminho_banco)
cursor = conn.cursor()

# Consulta os dados da tabela
cursor.execute('SELECT id, nome, preco FROM precos')
registros = cursor.fetchall()

# Exibe o relatório formatado
print(f"{'ID':<5} {'Produto':<30} {'Preço':>10}")
print('-' * 50)
for registro in registros:
    id, nome, preco = registro
    print(f"{id:<5} {nome:<30} R$ {preco:>8.2f}")

# Fecha a conexão
conn.close()
