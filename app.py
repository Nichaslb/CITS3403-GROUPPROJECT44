from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User  # 导入models.py中的db和User
from forms import LoginForm, RegisterForm
from functools import wraps
import os

app = Flask(__name__, 
           template_folder='template',
           static_url_path='',       # 移除URL前缀 // remove URL prefix
           static_folder='.')        # 使用项目根目录作为静态文件目录 // Use the project root directory as the static file directory

app.config['SECRET_KEY'] = os.urandom(24)

# 配置SQLAlchemy数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

# 确保在应用启动前创建所有数据库表
with app.app_context():
    db.create_all()
    print("Database tables created or confirmed.")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login', 'error')
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
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        
        if existing_user:
            flash('username or email already exsit', 'error')
            return render_template('signup.html', form=form)
        
        # 创建新用户 // Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )
        
        # 如果表单中有riot_id等字段，则保存这些信息 // If the form has riot_id etc. fields, save this information
        if 'riot_id' in request.form and 'tagline' in request.form and 'region' in request.form:
            riot_id = request.form['riot_id']
            tagline = request.form['tagline']
            region = request.form['region']
            if riot_id and tagline and region:
                new_user.riot_id = riot_id
                new_user.tagline = tagline
                new_user.region = region
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Sign up succeed! Now login...', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        password = form.password.data
        remember = True if request.form.get('remember') else False
        
        # 使用ORM查询用户
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            # 登录成功 // Login successful
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            
            # 设置会话持久性，如果"记住我"被选中，则为3天 // Set session persistence, if "remember me" is selected, then for 3 days
            if remember:
                session.permanent = True
                app.permanent_session_lifetime = 60 * 60 * 24 * 3  # 3天
            
            # 重定向到下一页或仪表板 // Redirect to the next page or dashboard
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')
            
            flash('Login success！', 'success')
            return redirect(next_page)
        else:
            flash('Username or password not correct', 'error')
    
    return render_template('signin.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('Log out!', 'info')
    return redirect(url_for('welcome'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/profile')
@login_required
def profile():
    # 使用ORM查询用户
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    # 使用ORM更新用户资料
    user = User.query.get(session['user_id'])
    
    user.riot_id = request.form.get('riot_id', '')
    user.tagline = request.form.get('tagline', '')
    user.region = request.form.get('region', '')
    
    db.session.commit()
    
    flash('Profile updated', 'success')
    return redirect(url_for('profile'))

@app.route('/share')
@login_required
def share():
    return render_template('share.html')

if __name__ == '__main__':
    app.run(debug=True)