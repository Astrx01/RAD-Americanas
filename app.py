from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from rastreador import get_info_americanas, salvar_preco_em_db

app = Flask(__name__)
app.secret_key = 'chave-secreta'

DB_PATH = 'db/precos.db'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/produtos')
def listar_produtos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT nome, url, precoDesejado, email, data
        FROM precos
        WHERE (nome, data) IN (
            SELECT nome, MAX(data)
            FROM precos
            GROUP BY nome
        )
        ORDER BY data DESC
    """)
    produtos = cursor.fetchall()
    conn.close()
    return render_template('lista.html', produtos=produtos)

@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar_produto():
    if request.method == 'POST':
        url = request.form['url']
        preco_desejado = request.form['preco_desejado']
        email = request.form['email']

        nome, preco_atual = get_info_americanas(url)
        if preco_atual:
            salvar_preco_em_db(nome, url, preco_atual, preco_desejado, email)
            flash(f'Produto "{nome}" adicionado com sucesso!', 'success')
            return redirect(url_for('listar_produtos'))
        else:
            flash('Não foi possível obter o preço do produto.', 'danger')
            return redirect(url_for('adicionar_produto'))

    return render_template('adicionar.html')

@app.route('/relatorio')
def relatorio():
    conn = sqlite3.connect('db/precos.db')
    cursor = conn.cursor()
    cursor.execute('SELECT nome, preco, data FROM precos ORDER BY nome, data DESC')
    registros = cursor.fetchall()
    conn.close()

    # Agrupa os registros por produto
    produtos = {}
    for nome, preco, data in registros:
        if nome not in produtos:
            produtos[nome] = []
        produtos[nome].append({'preco': preco, 'data': data})

    return render_template('relatorio.html', produtos=produtos)

@app.route('/produtos_monitorados')
def produtos_monitorados():
    return redirect(url_for('listar_produtos'))

if __name__ == "__main__":
    app.run(debug=True)
