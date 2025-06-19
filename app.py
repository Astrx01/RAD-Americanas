from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import sqlite3
from rastreador import get_info_americanas, salvar_preco_em_db
from werkzeug.security import generate_password_hash, check_password_hash
import plotly.graph_objects as go
from plotly.offline import plot
import subprocess

app = Flask(__name__)
app.secret_key = os.urandom(24)
DB_PATH = 'db/precos.db'

# Função para criar a tabela de usuários (se não existir)
def criar_tabela_usuarios():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Função para criar a tabela de precos (se não existir)
def criar_tabela_precos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS precos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            url TEXT NOT NULL,
            preco REAL NOT NULL,
            precoDesejado REAL NOT NULL,
            email TEXT,
            data DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER
        )
    """)
    conn.commit()
    conn.close()

criar_tabela_usuarios()
criar_tabela_precos()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
        if cursor.fetchone():
            flash('Nome de usuário já está em uso.', 'danger')
            conn.close()
            return render_template('register.html')

        hashed_password = generate_password_hash(password)

        try:
            cursor.execute("INSERT INTO usuarios (username, email, password) VALUES (?, ?, ?)", (username, email, hashed_password))  # Modificado
            conn.commit()
            flash('Cadastro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.Error as e:
            flash(f'Erro ao cadastrar usuário: {e}', 'danger')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT id, username, password FROM usuarios WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user:
            user_id, username, hashed_password = user
            if check_password_hash(hashed_password, password):
                session['user_id'] = user_id
                session['username'] = username
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Senha incorreta.', 'danger')
        else:
            flash('Usuário não encontrado.', 'danger')
        
        conn.close()

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('index'))

def login_required(f):
    def decorated_function(*args, **kwargs):
        if session.get('user_id') is None:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_produto():
    if request.method == 'POST':
        url = request.form['url']
        preco_desejado = request.form['preco_desejado']
        email = request.form['email']
        user_id = session['user_id']

        nome, preco_atual = get_info_americanas(url)
        if preco_atual is not None:
            try:
                preco_desejado = float(preco_desejado)
            except ValueError:
                flash('Preço desejado inválido. Insira um número.', 'danger')
                return redirect(url_for('adicionar_produto'))

            try:
                preco_atual = float(preco_atual)
            except ValueError:
                flash('Preço atual inválido. Não foi possível obter um número do site.', 'danger')
                return redirect(url_for('adicionar_produto'))

            salvar_preco_em_db(nome, url, preco_atual, preco_desejado, email, user_id)
            flash(f'Produto "{nome}" adicionado com sucesso!', 'success')
            return redirect(url_for('listar_produtos'))
        else:
            flash('Não foi possível obter o preço do produto.', 'danger')
            return redirect(url_for('adicionar_produto'))

    return render_template('adicionar.html')

def salvar_preco_em_db(nome, url, preco, preco_desejado, email, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO precos (nome, url, preco, precoDesejado, email, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nome, url, preco, preco_desejado, email, user_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Erro ao salvar no banco de dados: {e}")
    finally:
        conn.close()

@app.route('/produtos')
@login_required
def listar_produtos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    user_id = session['user_id']
    cursor.execute("""
       SELECT id, nome, url, CAST(preco AS REAL), precoDesejado, email, data
            FROM precos
            WHERE user_id = ?
            ORDER BY data DESC
    """, (user_id,))
    produtos = cursor.fetchall()
    conn.close()
    
    # Imprime os produtos para verificar os tipos de dados
    for produto in produtos:
        print(f"Produto: {produto}, Tipo do preço: {type(produto[2])}")
    
    return render_template('lista.html', produtos=produtos)

@app.route('/deletar/<path:nome>', methods=['POST'])
@login_required
def deletar_produto(nome):
    user_id = session['user_id']
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM precos WHERE nome = ? AND user_id = ?", (nome, user_id))
        conn.commit()
        flash(f'Produto "{nome}" e seu histórico foram deletados com sucesso!', 'success')
    except sqlite3.Error as e:
        flash(f'Erro ao deletar o produto do banco de dados: {e}', 'danger')
    finally:
        if conn:
            conn.close()

    return redirect(url_for('listar_produtos'))

@app.route('/relatorio')
@login_required
def relatorio():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT nome, preco, data
        FROM precos
        ORDER BY nome, data DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    # Agrupa por nome do produto
    produtos = {}
    for row in rows:
        nome = row['nome']
        consulta = {
            'preco': row['preco'],
            'data': row['data']
        }
        if nome not in produtos:
            produtos[nome] = []
        produtos[nome].append(consulta)

    return render_template('relatorio.html', produtos=produtos)

# Rota para exibir o formulário de edição
@app.route('/editar/<int:produto_id>', methods=['GET'])
@login_required
def editar_produto(produto_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    user_id = session['user_id']
    cursor.execute("SELECT id, nome, url, precoDesejado, email FROM precos WHERE id = ? AND user_id = ?", (produto_id, user_id))
    produto = cursor.fetchone()
    conn.close()

    if produto:
        return render_template('editar.html', produto=produto)
    else:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('listar_produtos'))

# Rota para processar a edição
@app.route('/atualizar/<int:produto_id>', methods=['POST'])
@login_required
def atualizar_produto(produto_id):
    nome = request.form['nome']
    url = request.form['url']
    preco_desejado = request.form['preco_desejado']
    email = request.form['email']

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE precos
        SET nome = ?, url = ?, precoDesejado = ?, email = ?
        WHERE id = ?
    """, (nome, url, preco_desejado, email, produto_id))
    conn.commit()
    conn.close()
    flash('Produto atualizado com sucesso!', 'success')
    return redirect(url_for('listar_produtos'))

@app.route('/graficos')
@login_required
def graficos():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT nome, preco, data
        FROM precos
        ORDER BY nome, data
    """)
    rows = cursor.fetchall()
    conn.close()

    # Organiza os dados por produto
    produtos = {}
    for nome, preco, data in rows:
        if nome not in produtos:
            produtos[nome] = {'datas': [], 'precos': []}
        produtos[nome]['datas'].append(data)
        produtos[nome]['precos'].append(preco)

    # Gera um gráfico Plotly para cada produto
    from plotly.offline import plot
    import plotly.graph_objs as go
    graficos_html = {}
    for nome, valores in produtos.items():
        fig = go.Figure(data=[go.Scatter(
            x=valores['datas'],
            y=valores['precos'],
            mode='lines+markers',
            name=nome
        )])
        fig.update_layout(title=f'Histórico de Preços de {nome}', xaxis_title='Data', yaxis_title='Preço (R$)')
        graficos_html[nome] = plot(fig, output_type='div')

    return render_template('graficos.html', graficos_html=graficos_html)

# Nova rota para a tela de gráficos dos produtos pesquisados
@app.route('/graficos_pesquisa')
@login_required
def graficos_pesquisa():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    user_id = session['user_id']
    cursor.execute('SELECT nome, preco, data FROM precos WHERE user_id = ? ORDER BY nome, data DESC', (user_id,))
    registros = cursor.fetchall()
    conn.close()

    produtos = {}
    for nome, preco, data in registros:
        if nome not in produtos:
            produtos[nome] = {'precos': [], 'datas': []}
        produtos[nome]['precos'].append(preco)
        produtos[nome]['datas'].append(data)

    # Gerar gráficos para cada produto
    graficos_html = {}
    for nome, dados in produtos.items():
        fig = go.Figure(data=[go.Scatter(x=dados['datas'], y=dados['precos'], mode='lines+markers')])
        fig.update_layout(title=f'Histórico de Preços de {nome}', xaxis_title='Data', yaxis_title='Preço')
        graficos_html[nome] = plot(fig, output_type='div')

    return render_template('graficos_pesquisa.html', graficos_html=graficos_html)

@app.route('/iniciar_timer', methods=['POST'])
@login_required
def iniciar_timer():
    try:
        subprocess.Popen(['python', 'timer.py'])
        flash('Timer iniciado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao iniciar o timer: {e}', 'danger')
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)