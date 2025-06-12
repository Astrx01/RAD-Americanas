
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
    cursor.execute("SELECT nome, url, precoDesejado, email, MAX(data) FROM precos GROUP BY nome, url, precoDesejado, email")
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

if __name__ == "__main__":
    app.run(debug=True)
