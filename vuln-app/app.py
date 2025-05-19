from flask import Flask, request, render_template, redirect, url_for, jsonify, session, make_response, send_from_directory
import sqlite3
import os
import json
import random
import string
from werkzeug.security import generate_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'chave_super_secreta_nao_mude_em_producao'  # VULN-HARDCODED-SECRET

# Configuração do banco de dados
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

# Configuração das flags para os desafios
FLAGS = {
    'idor_challenge': 'FLAG{1D0R_4DM1N_4CC3SS}',
    'sqli_challenge': 'FLAG{SQL_1NJ3CT10N_M4ST3R}',
    'xss_challenge': 'FLAG{CR0SS_S1T3_SCR1PT1NG}',
    'bruteforce_challenge': 'FLAG{W34K_P4SSW0RD_P0L1CY}',
    'support_challenge': 'FLAG{SUPP0RT_4CC0UNT_C0MPR0M1S3D}',
    'api_token_challenge': 'FLAG{S3CR3T_4P1_T0K3N_L34K3D}'
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Criação das tabelas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        email TEXT,
        bio TEXT,
        private_notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gallery (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        image_url TEXT,
        description TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        token TEXT,
        description TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Nova tabela para rastrear flags conquistadas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_flags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        challenge_id TEXT,
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Inserir dados iniciais
    users = [
        (1, 'admin', 'admin123', 1),  # VULN-WEAK-CREDENTIALS
        (2, 'user1', 'password123', 0),
        (3, 'user2', 'qwerty', 0),
        (4, 'support', 'support123', 0)  # Conta de suporte para o desafio
    ]
    
    profiles = [
        (1, 1, 'Administrador', 'admin@vuln-app.lab.local', 'Administrador do sistema', 'Senha do servidor: S3rv3rP@ss! FLAG{1D0R_4DM1N_4CC3SS}'),
        (2, 2, 'Usuário Um', 'user1@example.com', 'Usuário comum', 'Notas pessoais'),
        (3, 3, 'Usuário Dois', 'user2@example.com', 'Outro usuário', 'Mais notas pessoais'),
        (4, 4, 'Suporte Técnico', 'support@vuln-app.lab.local', 'Conta de suporte técnico', 'Senha temporária para acesso ao sistema: support123')
    ]
    
    gallery = [
        (1, 1, 'Dashboard Admin', '/static/images/dashboard.jpg', 'Painel administrativo'),
        (2, 2, 'Minha foto', '/static/images/user1.jpg', 'Foto de perfil'),
        (3, 3, 'Férias', '/static/images/vacation.jpg', 'Foto das férias')
    ]
    
    api_tokens = [
        (1, 1, 'a1b2c3d4e5f6g7h8i9j0', 'Token de API para acesso administrativo - FLAG{S3CR3T_4P1_T0K3N_L34K3D}'),
        (2, 2, 'user1token123456789', 'Token de API para usuário comum'),
        (3, 4, 'supporttoken987654321', 'Token de API para suporte técnico - FLAG{SUPP0RT_4CC0UNT_C0MPR0M1S3D}')
    ]
    
    # Verificar se já existem dados
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", users)
        cursor.executemany("INSERT INTO profiles VALUES (?, ?, ?, ?, ?, ?)", profiles)
        cursor.executemany("INSERT INTO gallery VALUES (?, ?, ?, ?, ?)", gallery)
        cursor.executemany("INSERT INTO api_tokens VALUES (?, ?, ?, ?)", api_tokens)
    
    conn.commit()
    conn.close()

# Inicializar o banco de dados
init_db()

# Middleware para verificar autenticação
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Middleware para verificar se é admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            return jsonify({"error": "Acesso não autorizado"}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # VULN-SQLI: Concatenação direta de entrada do usuário na query SQL
        query = f"SELECT id, username, is_admin FROM users WHERE username = '{username}' AND password = '{password}'"
        
        try:
            cursor.execute(query)
            user = cursor.fetchone()
            
            if user:
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['is_admin'] = user[2]
                
                # Flag para o desafio de brute force
                if user[0] == 1:  # Se for o admin
                    return redirect(url_for('admin_panel'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                error = 'Credenciais inválidas. Tente novamente.'
        except sqlite3.Error as e:
            # Mostrar o erro para facilitar a exploração
            error = f"Erro SQL: {str(e)}"
        
        conn.close()
    
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    success = None
    user_id = None
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if not username or not password:
            error = 'Nome de usuário e senha são obrigatórios.'
        else:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Verificar se o usuário já existe
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                error = 'Nome de usuário já existe. Escolha outro.'
            else:
                # Inserir novo usuário
                cursor.execute(
                    "INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                    (username, password, 0)
                )
                conn.commit()
                
                # Obter o ID do usuário recém-criado
                cursor.execute("SELECT last_insert_rowid()")
                user_id = cursor.fetchone()[0]
                
                # Criar perfil básico
                cursor.execute(
                    "INSERT INTO profiles (user_id, name, email, bio, private_notes) VALUES (?, ?, ?, ?, ?)",
                    (user_id, username, email, 'Novo usuário', 'Minhas notas privadas')
                )
                conn.commit()
                
                success = f'Registro bem-sucedido! Seu ID de usuário é: {user_id}'
            
            conn.close()
    
    return render_template('register.html', error=error, success=success, user_id=user_id)

@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Obter informações do usuário
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    
    # Obter itens da galeria
    cursor.execute("SELECT * FROM gallery WHERE user_id = ?", (session['user_id'],))
    gallery_items = cursor.fetchall()
    
    # Obter flags conquistadas
    cursor.execute("SELECT challenge_id FROM user_flags WHERE user_id = ?", (session['user_id'],))
    completed_challenges = [row[0] for row in cursor.fetchall()]
    
    # Calcular pontuação
    points = len(completed_challenges) * 100
    
    # Obter ranking
    cursor.execute("""
        SELECT u.username, COUNT(f.id) as flags_count
        FROM users u
        LEFT JOIN user_flags f ON u.id = f.user_id
        GROUP BY u.id
        ORDER BY flags_count DESC
        LIMIT 5
    """)
    leaderboard = cursor.fetchall()
    
    conn.close()
    
    return render_template(
        'dashboard.html', 
        user_id=session['user_id'],
        username=session['username'],
        is_admin=session['is_admin'],
        gallery_items=gallery_items,
        completed_challenges=completed_challenges,
        points=points,
        leaderboard=leaderboard
    )

@app.route('/products')
def products():
    category = request.args.get('category', 'all')
    released = request.args.get('released', '1')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Criar tabela de produtos se não existir
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        price REAL,
        released INTEGER DEFAULT 1
    )
    ''')
    
    # Inserir produtos de exemplo se não existirem
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        products_data = [
            ('Smartphone X', 'Electronics', 999.99, 1),
            ('Laptop Pro', 'Electronics', 1499.99, 1),
            ('Coffee Mug', 'Gifts', 19.99, 1),
            ('Secret Product', 'Hidden', 9999.99, 0),
            ('Unreleased Gadget', 'Electronics', 599.99, 0),
            ('New Console 2026', 'Gaming', 499.99, 0)
        ]
        cursor.executemany(
            "INSERT INTO products (name, category, price, released) VALUES (?, ?, ?, ?)",
            products_data
        )
        conn.commit()
    
    # VULN-SQLI: Concatenação direta de entrada do usuário na query SQL
    if category == 'all':
        sql_query = f"SELECT * FROM products WHERE released = {released}"
    else:
        sql_query = f"SELECT * FROM products WHERE category = '{category}' AND released = {released}"
    
    try:
        cursor.execute(sql_query)
        products = cursor.fetchall()
        error = None
    except sqlite3.Error as e:
        products = []
        error = str(e)
        # Adicionar a flag no erro para facilitar a descoberta
        if "syntax error" in error.lower():
            error += " FLAG{SQL_1NJ3CT10N_M4ST3R}"
    
    conn.close()
    
    return render_template('products.html', products=products, category=category, error=error)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # VULN-SQLI: Concatenação direta de entrada do usuário na query SQL
    sql_query = f"SELECT id, title, description FROM gallery WHERE title LIKE '%{query}%' OR description LIKE '%{query}%'"
    
    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()
        error = None
    except sqlite3.Error as e:
        results = []
        error = str(e)
        # Adicionar a flag no erro para facilitar a descoberta
        if "syntax error" in error.lower():
            error += " FLAG{SQL_1NJ3CT10N_M4ST3R}"
    
    conn.close()
    
    return render_template('search_results.html', query=query, results=results, error=error)

@app.route('/comment')
def comment():
    text = request.args.get('text', '')
    
    # VULN-XSS: Retorno direto da entrada do usuário sem sanitização
    # Adicionar a flag em um comentário HTML para facilitar a descoberta
    flag_comment = "<!-- FLAG{CR0SS_S1T3_SCR1PT1NG} -->"
    
    return render_template('comment.html', comment_text=text, flag_comment=flag_comment)

@app.route('/user/<int:user_id>/profile')
@login_required
def user_profile(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # VULN-IDOR: Não verifica se o usuário tem permissão para acessar o perfil
    cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
    profile = cursor.fetchone()
    
    conn.close()
    
    if profile:
        return render_template('profile.html', profile=profile)
    else:
        return "Perfil não encontrado", 404

@app.route('/api/user/<int:user_id>/profile')
@login_required
def get_user_profile(user_id):
    # VULN-IDOR: Não verifica se o usuário tem permissão para acessar o perfil
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
    profile = cursor.fetchone()
    
    cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    conn.close()
    
    if profile:
        profile_data = {
            "id": profile[0],
            "user_id": profile[1],
            "name": profile[2],
            "email": profile[3],
            "bio": profile[4],
            "private_notes": profile[5],  # VULN-DATA-LEAK: Expõe notas privadas
            "is_admin": user[0] if user else 0
        }
        return jsonify(profile_data)
    else:
        return jsonify({"error": "Perfil não encontrado"}), 404

@app.route('/api/tokens')
@login_required
def api_tokens():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Obter tokens do usuário atual
    cursor.execute("SELECT * FROM api_tokens WHERE user_id = ?", (session['user_id'],))
    tokens = cursor.fetchall()
    
    conn.close()
    
    return render_template('api_tokens.html', tokens=tokens)

@app.route('/api/secret')
def api_secret():
    # Página secreta que contém informações sobre tokens de API
    return render_template('api_secret.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin_panel():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    conn.close()
    
    # Adicionar a flag para o desafio de brute force
    flag = FLAGS['bruteforce_challenge']
    
    return render_template('admin.html', users=users, flag=flag)

@app.route('/admin-panel.html')
def admin_panel_hidden():
    # Página secreta mencionada no robots.txt
    if 'user_id' in session and session.get('is_admin'):
        return redirect(url_for('admin'))
    else:
        return render_template('admin.html', error="Acesso não autorizado. Você precisa ser um administrador.")

@app.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt')

@app.route('/api/submit_flag', methods=['POST'])
@login_required
def submit_flag():
    challenge_id = request.form.get('challenge_id')
    flag = request.form.get('flag')
    
    if not challenge_id or not flag:
        return jsonify({"success": False, "message": "Parâmetros inválidos"})
    
    # Verificar se a flag está correta
    if challenge_id in FLAGS and FLAGS[challenge_id] == flag:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar se o usuário já completou este desafio
        cursor.execute(
            "SELECT id FROM user_flags WHERE user_id = ? AND challenge_id = ?", 
            (session['user_id'], challenge_id)
        )
        
        if not cursor.fetchone():
            # Registrar a flag conquistada
            cursor.execute(
                "INSERT INTO user_flags (user_id, challenge_id) VALUES (?, ?)",
                (session['user_id'], challenge_id)
            )
            conn.commit()
        
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": "Flag correta! Pontos adicionados ao seu perfil."
        })
    else:
        return jsonify({
            "success": False, 
            "message": "Flag incorreta. Tente novamente."
        })

@app.route('/profile')
@login_required
def profile():
    # Redirecionar para a nova rota que mostra o ID na URL
    return redirect(url_for('user_profile', user_id=session['user_id']))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # VULN-DEBUG-MODE
