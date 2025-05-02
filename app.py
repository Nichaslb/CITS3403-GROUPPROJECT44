from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from forms import LoginForm, RegisterForm
from functools import wraps
import os

app = Flask(__name__, 
           template_folder='template',
           static_url_path='',       # 移除URL前缀 // remove URL prefix
           static_folder='.')        # 使用项目根目录作为静态文件目录 // Use the project root directory as the static file directory

app.config['SECRET_KEY'] = os.urandom(24)
app.config['DATABASE'] = 'users.db'

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db_connection()
        with open('schema.sql') as f:
            db.executescript(f.read())
        db.commit()
        db.close()
        print("Database initialized successfully.")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录以访问该页面', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def welcome():
    return render_template('landing-page.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        
        # 检查用户名或邮箱是否已存在 // Check if username or email already exists
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?',
                          (username, email)).fetchone()
        
        if user:
            flash('用户名或邮箱已存在', 'error')
            conn.close()
            return render_template('signup.html', form=form)
        
        # 创建新用户 // Create new user
        hashed_password = generate_password_hash(password)
        conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                   (username, email, hashed_password))
        
        # 如果表中有riot_id和region字段，则保存这些信息 // If the table has riot_id and region fields, save this information
        if 'riot_id' in request.form and 'tagline' in request.form and 'region' in request.form:
            riot_id = request.form['riot_id']
            tagline = request.form['tagline']
            region = request.form['region']
            if riot_id and tagline and region:
                user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
                try:
                    conn.execute('UPDATE users SET riot_id = ?, tagline = ?, region = ? WHERE id = ?',
                               (riot_id, tagline, region, user_id))
                except sqlite3.OperationalError:
                    # 如果表中没有这些字段，忽略错误 // Ignore the error if these fields do not exist
                    pass
        
        conn.commit()
        conn.close()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        password = form.password.data
        remember = True if request.form.get('remember') else False
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            # 登录成功 // Login successful
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            
            # 设置会话持久性，如果"记住我"被选中，则为3天 // Set session persistence, if "remember me" is selected, then for 3 days
            if remember:
                session.permanent = True
                app.permanent_session_lifetime = 60 * 60 * 24 * 3  # 3天
            
            # 重定向到下一页或仪表板 // Redirect to the next page or dashboard
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')
            
            flash('登录成功！', 'success')
            return redirect(next_page)
        else:
            flash('用户名或密码不正确', 'error')
    
    return render_template('signin.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('您已成功退出登录', 'info')
    return redirect(url_for('welcome'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/profile')
@login_required
def profile():
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', 
                      (session['user_id'],)).fetchone()
    conn.close()
    return render_template('profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    riot_id = request.form.get('riot_id', '')
    tagline = request.form.get('tagline', '')
    region = request.form.get('region', '')
    
    conn = get_db_connection()
    conn.execute('UPDATE users SET riot_id = ?, tagline = ?, region = ? WHERE id = ?',
               (riot_id, tagline, region, session['user_id']))
    conn.commit()
    conn.close()
    
    flash('个人资料已更新', 'success')
    return redirect(url_for('profile'))

# 以下是您正在使用的路由，保留share路由以保证兼容性 // The following are the routes you are using, keeping the share route for compatibility
@app.route('/share')
@login_required
def share():
    return render_template('share.html')

if __name__ == '__main__':
    # 强制初始化数据库 // Force database initialization
    print("Attempting to initialize database...")
    if not os.path.exists(app.config['DATABASE']):
        init_db()
        print("Database created.")
    else:
        # 即使数据库文件存在，也重新初始化表结构 // Reinitialize the table structure even if the database file exists
        os.remove(app.config['DATABASE'])
        init_db()
        print("Database recreated.")
    app.run(debug=True)