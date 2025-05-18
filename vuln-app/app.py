from flask import Flask, request, render_template, redirect, url_for, jsonify, session, make_response
import sqlite3
import os
import json
from werkzeug.security import generate_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'chave_super_secreta_nao_mude_em_producao'  # VULN-HARDCODED-SECRET

# Configuração do banco de dados
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

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
    
    # Inserir dados iniciais
    users = [
        (1, 'admin', 'admin123', 1),  # VULN-WEAK-CREDENTIALS
        (2, 'user1', 'password123', 0),
        (3, 'user2', 'qwerty', 0)
    ]
    
    profiles = [
        (1, 1, 'Administrador', 'admin@vuln-app.lab.local', 'Administrador do sistema', 'Senha do servidor: S3rv3rP@ss!'),
        (2, 2, 'Usuário Um', 'user1@example.com', 'Usuário comum', 'Notas pessoais'),
        (3, 3, 'Usuário Dois', 'user2@example.com', 'Outro usuário', 'Mais notas pessoais')
    ]
    
    gallery = [
        (1, 1, 'Dashboard Admin', '/static/images/dashboard.jpg', 'Painel administrativo'),
        (2, 2, 'Minha foto', '/static/images/user1.jpg', 'Foto de perfil'),
        (3, 3, 'Férias', '/static/images/vacation.jpg', 'Foto das férias')
    ]
    
    # Verificar se já existem dados
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", users)
        cursor.executemany("INSERT INTO profiles VALUES (?, ?, ?, ?, ?, ?)", profiles)
        cursor.executemany("INSERT INTO gallery VALUES (?, ?, ?, ?, ?)", gallery)
    
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
    return render_template('index.html')

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
        cursor.execute(query)
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = user[2]
            return redirect(url_for('dashboard'))
        else:
            error = 'Credenciais inválidas. Tente novamente.'
    
    return render_template('login.html', error=error)

@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM gallery WHERE user_id = ?", (session['user_id'],))
    gallery_items = cursor.fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', gallery_items=gallery_items)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # VULN-SQLI: Concatenação direta de entrada do usuário na query SQL
    sql_query = f"SELECT id, title, description FROM gallery WHERE title LIKE '%{query}%' OR description LIKE '%{query}%'"
    cursor.execute(sql_query)
    results = cursor.fetchall()
    
    conn.close()
    
    return render_template('search_results.html', query=query, results=results)

@app.route('/comment')
def comment():
    text = request.args.get('text', '')
    
    # VULN-XSS: Retorno direto da entrada do usuário sem sanitização
    return render_template('comment.html', comment_text=text)

@app.route('/api/user/<int:user_id>/profile')
@login_required
def get_user_profile(user_id):
    # VULN-IDOR: Não verifica se o usuário tem permissão para acessar o perfil
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
    profile = cursor.fetchone()
    
    conn.close()
    
    if profile:
        profile_data = {
            "id": profile[0],
            "user_id": profile[1],
            "name": profile[2],
            "email": profile[3],
            "bio": profile[4],
            "private_notes": profile[5]  # VULN-DATA-LEAK: Expõe notas privadas
        }
        return jsonify(profile_data)
    else:
        return jsonify({"error": "Perfil não encontrado"}), 404

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
    
    return render_template('admin.html', users=users)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # VULN-DEBUG-MODE
