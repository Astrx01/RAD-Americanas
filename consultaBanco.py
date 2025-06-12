import sqlite3

# Caminho para o banco de dados
caminho_banco = 'db/precos.db'

# Conecta ao banco
conn = sqlite3.connect(caminho_banco)
cursor = conn.cursor()

# Consulta os dados da tabela
cursor.execute('SELECT * FROM precos')
registros = cursor.fetchall()

# Exibe os dados
for registro in registros:
    print(registro)

# Fecha a conexão
conn.close()
