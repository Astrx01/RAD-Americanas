from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from rastreador import get_info_americanas, salvar_preco_em_db
import  os

app = Flask(__name__)
app.secret_key = 'chave-secreta'
app.secret_key = os.urandom(24)  # Chave secreta para a sessão

DB_PATH = 'db/precos.db'# Dados de exemplo para autenticação (substitua por um banco de dados)
USUARIOS = {
    'admin': 'senha123'
}

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in USUARIOS:
            flash('Nome de usuário já está em uso.', 'danger')
            return render_template('register.html')

        USUARIOS[username] = password  # Armazena o usuário e senha
        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in USUARIOS and USUARIOS[username] == password:
            session['username'] = username
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos.', 'danger')
            return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('index'))


# Decorator para verificar se o usuário está logado
def login_required(f):
    def decorated_function(*args, **kwargs):
        if session.get('username') is None:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function




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

# --- NOVA ROTA PARA DELETAR ---
@app.route('/deletar/<path:nome>', methods=['POST'])
def deletar_produto(nome):
    """
    Deleta um produto e todo o seu histórico de preços do banco de dados.
    Usa o método POST por segurança, para evitar exclusão acidental por crawlers.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Deleta todos os registros com o nome do produto especificado
        cursor.execute("DELETE FROM precos WHERE nome = ?", (nome,))
        conn.commit()
        flash(f'Produto "{nome}" e seu histórico foram deletados com sucesso!', 'success')
    except sqlite3.Error as e:
        flash(f'Erro ao deletar o produto do banco de dados: {e}', 'danger')
    finally:
        if conn:
            conn.close()
            
    return redirect(url_for('listar_produtos'))


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
