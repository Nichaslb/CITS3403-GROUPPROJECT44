from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import requests
import time
from functools import wraps
from flask_migrate import Migrate

from flask_login import login_required, current_user


# 从models导入数据库模型
from models import db, User, GameModeStats, MatchRecord, Friend, Guides , SharedGuide # 确保从models导入Friend
from forms import LoginForm, RegisterForm
from routes.riot_api import fetch_puuid, fetch_rank_info, fetch_match_list, fetch_match_details, get_api_key

app = Flask(__name__, 
           template_folder='template',
           static_url_path='',       # 移除URL前缀 // remove URL prefix
           static_folder='.')        # 使用项目根目录作为静态文件目录 // Use the project root directory as the static file directory

app.config['SECRET_KEY'] = os.urandom(24)

# 配置SQLAlchemy数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 设置Riot API密钥（如果需要从环境变量获取）
app.config['RIOT_API_KEY'] = os.environ.get('RIOT_API_KEY', '')

# 初始化数据库
db.init_app(app)

migrate = Migrate(app, db)

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
            # 更新最后登录时间
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # 登录成功
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            
            # 设置会话持久性，如果"记住我"被选中，则为3天 // Set session persistence, if "remember me" is selected, then for 3 days
            if remember:
                session.permanent = True
                app.permanent_session_lifetime = 60 * 60 * 24 * 3  # 3天 3 days
            
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

@app.route('/friends')
@login_required
def friends():
    # 获取当前用户
    user = User.query.get(session['user_id'])
    return render_template('friends.html', user=user)

@app.route('/guide')
@login_required
def guide():
    return render_template('guide.html')

@app.route('/patchnotes')
def patchnotes():
    return render_template('patchnotes.html')


@app.route('/characters')
def characters():
    return render_template('characters.html')


@app.route('/create_guide')
def create_guide():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    return render_template('create_guide.html', user=user)


@app.route('/guide_inbox')
@login_required
def guide_inbox():
    return render_template('guide_inbox.html')

@app.route('/user_guide')
def user_guide():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    guides = user.guides.order_by(Guides.created_at.desc()).all()
    return render_template('user_guide.html', user=user, guides=guides, username=user.username)


@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    # 获取表单数据
    riot_id = request.form.get('riot_id', '')
    tagline = request.form.get('tagline', '')
    region = request.form.get('region', '')
    
    # 获取当前用户
    user = User.query.get(session['user_id'])
    
    # 检查Riot ID和tagline是否有变化
    riot_id_changed = user.riot_id != riot_id
    tagline_changed = user.tagline != tagline
    
    # 更新用户资料
    user.riot_id = riot_id
    user.tagline = tagline
    user.region = region
    
    # 如果Riot ID或tagline有变化，且都不为空，则尝试获取新的PUUID
    if (riot_id_changed or tagline_changed) and riot_id and tagline:
        api_key = get_api_key()
        if api_key:
            result = fetch_puuid(riot_id, tagline, api_key)
            if "puuid" in result:
                # 更新用户的PUUID字段
                user.puuid = result["puuid"]
                flash('Riot账号已验证', 'success')
            elif "error" in result:
                flash(f'Riot账号信息验证失败: {result["error"]}', 'error')
                # 仍然保存用户输入的信息，但提示验证失败
    
    db.session.commit()
    
    flash('个人资料已更新', 'success')
    return redirect(url_for('profile'))

@app.route('/share')
@login_required
def share():
    return render_template('share.html')

@app.route('/api/puuid')
@login_required
def api_get_puuid():
    """获取当前登录用户的PUUID"""
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({"status": "error", "message": "找不到用户信息"}), 404
    
    # 验证用户是否设置了riot_id和tagline
    if not user.riot_id or not user.tagline:
        return jsonify({
            "status": "error", 
            "message": "未设置Riot ID或Tagline，请先更新个人资料",
            "needsUpdate": True
        }), 400
    
    # 获取API密钥
    api_key = get_api_key()
    if not api_key:
        return jsonify({"status": "error", "message": "无法获取API密钥"}), 500
    
    # 调用Riot API获取PUUID
    result = fetch_puuid(user.riot_id, user.tagline, api_key)
    
    if "error" in result:
        return jsonify({"status": "error", "message": result["error"]}), 400
    
    # 如果用户模型有PUUID字段，更新它
    if hasattr(user, 'puuid'):
        user.puuid = result.get("puuid")
        db.session.commit()
    
    return jsonify({
        "status": "success", 
        "data": result
    })

# 添加一个API路由用于获取用户游戏数据
@app.route('/api/game_profile')
@login_required
def api_game_profile():
    """获取用户游戏资料，包括PUUID、段位信息等"""
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({"status": "error", "message": "找不到用户信息"}), 404
    
    # 验证用户是否设置了riot_id和tagline
    if not user.riot_id or not user.tagline:
        return jsonify({
            "status": "error", 
            "message": "未设置Riot ID或Tagline，请先更新个人资料",
            "needsUpdate": True
        }), 400
    
    # 获取API密钥
    api_key = get_api_key()
    if not api_key:
        return jsonify({"status": "error", "message": "无法获取API密钥"}), 500
    
    # 获取PUUID
    puuid_result = fetch_puuid(user.riot_id, user.tagline, api_key)
    if "error" in puuid_result:
        return jsonify({"status": "error", "message": puuid_result["error"]}), 400
    
    puuid = puuid_result["puuid"]
    
    # 获取段位信息
    rank_info = fetch_rank_info(puuid, api_key)
    
    # 获取最近的比赛列表
    match_list = fetch_match_list(puuid, 5, api_key)
    
    # 返回组合数据
    return jsonify({
        "status": "success",
        "data": {
            "account": puuid_result,
            "rank": rank_info if not isinstance(rank_info, dict) or "error" not in rank_info else None,
            "matches": match_list if not isinstance(match_list, dict) or "error" not in match_list else []
        }
    })

@app.route('/api/analyze_game_modes', methods=['POST'])
@login_required
def api_analyze_game_modes():
    """触发分析当前用户最近30场对局的游戏模式"""
    from routes.algorithm import analyze_game_modes
    
    user_id = session.get('user_id')
    if not user_id:
        print("用户未登录，无法分析游戏模式")
        return jsonify({"status": "error", "message": "用户未登录"}), 401
    
    print(f"开始为用户 {user_id} 分析游戏模式")
    result = analyze_game_modes(user_id)
    print(f"游戏模式分析完成，状态: {result['status']}")
    return jsonify(result)

@app.route('/api/game_modes_stats')
@login_required
def api_game_modes_stats():
    """获取当前用户的游戏模式统计数据"""
    user_id = session.get('user_id')
    if not user_id:
        print("用户未登录，无法获取游戏模式统计")
        return jsonify({"status": "error", "message": "用户未登录"}), 401
    
    print(f"正在查询用户 {user_id} 的游戏模式统计")
    stats = GameModeStats.query.filter_by(user_id=user_id).first()
    if not stats:
        print(f"用户 {user_id} 尚未分析游戏模式数据")
        return jsonify({
            "status": "error", 
            "message": "尚未分析游戏模式数据",
            "needsAnalysis": True
        }), 404
    
    # 检查数据是否过时
    now = datetime.utcnow()
    if (now - stats.last_updated).days > 1:  # 如果数据超过1天
        print(f"用户 {user_id} 的游戏模式数据已过时，最后更新: {stats.last_updated}")
        return jsonify({
            "status": "success",
            "data": {
                "sr_5v5_percentage": stats.sr_5v5_percentage,
                "aram_percentage": stats.aram_percentage,
                "fun_modes_percentage": stats.fun_modes_percentage,
                "bot_games_percentage": stats.bot_games_percentage,
                "custom_percentage": stats.custom_percentage,
                "unknown_percentage": stats.unknown_percentage,
                "total_matches": stats.total_matches,
                "last_updated": stats.last_updated.strftime("%Y-%m-%d %H:%M:%S")
            },
            "needsUpdate": True
        })
    
    print(f"成功获取用户 {user_id} 的游戏模式统计，共 {stats.total_matches} 场比赛")
    return jsonify({
        "status": "success",
        "data": {
            "sr_5v5_percentage": stats.sr_5v5_percentage,
            "aram_percentage": stats.aram_percentage,
            "fun_modes_percentage": stats.fun_modes_percentage,
            "bot_games_percentage": stats.bot_games_percentage,
            "custom_percentage": stats.custom_percentage,
            "unknown_percentage": stats.unknown_percentage,
            "total_matches": stats.total_matches,
            "last_updated": stats.last_updated.strftime("%Y-%m-%d %H:%M:%S")
        }
    })

@app.route('/api/recent_matches')
@login_required
def api_recent_matches():
    """获取用户最近的对局记录"""
    user_id = session.get('user_id')
    if not user_id:
        print("用户未登录，无法获取最近对局")
        return jsonify({"status": "error", "message": "用户未登录"}), 401
    
    print(f"正在查询用户 {user_id} 的最近对局记录")
    # 获取最近30场对局记录
    matches = MatchRecord.query.filter_by(user_id=user_id).order_by(MatchRecord.game_date.desc()).limit(30).all()
    
    match_list = [{
        "match_id": match.match_id,
        "queue_id": match.queue_id,
        "game_mode": match.game_mode,
        "category": match.game_category,
        "date": match.game_date.strftime("%Y-%m-%d %H:%M:%S")
    } for match in matches]
    
    print(f"成功获取用户 {user_id} 的 {len(match_list)} 场最近对局")
    return jsonify({
        "status": "success",
        "data": match_list
    })

@app.route('/api/search_user', methods=['GET'])
@login_required
def api_search_user():
    """通过用户名搜索其他用户"""
    search_term = request.args.get('query', '')
    username = request.args.get('username', '')
    exact = request.args.get('exact', 'false').lower() == 'true'
    
    # 使用 username 参数或者 query 参数
    search_value = username or search_term
    
    if not search_value:
        return jsonify({
            "status": "error", 
            "message": "请提供搜索条件"
        }), 400
    
    # 搜索用户（避免搜索到当前用户）
    current_user_id = session.get('user_id')
    
    if exact:
        # 精确匹配
        users = User.query.filter(
            User.id != current_user_id,
            User.username == search_value
        ).limit(10).all()
    else:
        # 模糊匹配
        users = User.query.filter(
            User.id != current_user_id,
            User.username.like(f'%{search_value}%')
        ).limit(10).all()
    
    user_list = [{
        "id": user.id,
        "username": user.username,
        "riot_id": user.riot_id,
        "tagline": user.tagline,
        "region": user.region
    } for user in users]
    
    return jsonify({
        "status": "success",
        "data": user_list
    })

@app.route('/api/friends')
@login_required
def api_get_friends():
    """获取当前用户的好友列表"""
    current_user_id = session.get('user_id')
    
    # 查询好友关系
    friends = Friend.query.filter_by(user_id=current_user_id).all()
    
    friend_list = []
    for friend_rel in friends:
        # 获取好友的用户信息
        friend = User.query.get(friend_rel.friend_id)
        if friend:
            friend_list.append({
                "id": friend.id,
                "username": friend.username,
                "riot_id": friend.riot_id,
                "tagline": friend.tagline,
                "region": friend.region,
                "last_login": friend.last_login.isoformat() if friend.last_login else None
            })
    
    return jsonify({
        "status": "success",
        "data": friend_list
    })

@app.route('/api/add_friend', methods=['POST'])
@login_required
def api_add_friend():
    """添加好友"""
    friend_id = request.json.get('friend_id')
    
    if not friend_id:
        return jsonify({"status": "error", "message": "未提供好友ID"}), 400
    
    current_user_id = session.get('user_id')
    
    # 检查是否已经是好友
    existing = Friend.query.filter_by(
        user_id=current_user_id, 
        friend_id=friend_id
    ).first()
    
    if existing:
        return jsonify({"status": "error", "message": "已经是好友"}), 400
    
    # 检查用户是否存在
    friend = User.query.get(friend_id)
    if not friend:
        return jsonify({"status": "error", "message": "用户不存在"}), 404
    
    # 添加好友关系
    new_friend = Friend(user_id=current_user_id, friend_id=friend_id)
    db.session.add(new_friend)
    
    # 互相添加（可选）
    new_friend_back = Friend(user_id=friend_id, friend_id=current_user_id)
    db.session.add(new_friend_back)
    
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "message": f"已添加 {friend.username} 为好友"
    })

@app.route('/api/remove_friend', methods=['POST'])
@login_required
def api_remove_friend():
    """删除好友"""
    friend_id = request.json.get('friend_id')
    
    if not friend_id:
        return jsonify({"status": "error", "message": "未提供好友ID"}), 400
    
    current_user_id = session.get('user_id')
    
    # 查找好友关系
    friend_rel = Friend.query.filter_by(
        user_id=current_user_id, 
        friend_id=friend_id
    ).first()
    
    if not friend_rel:
        return jsonify({"status": "error", "message": "好友关系不存在"}), 404
    
    # 获取好友用户名
    friend = User.query.get(friend_id)
    friend_username = friend.username if friend else "未知用户"
    
    # 删除好友关系
    db.session.delete(friend_rel)
    
    # 删除对方的好友关系（如果存在）
    friend_rel_back = Friend.query.filter_by(
        user_id=friend_id, 
        friend_id=current_user_id
    ).first()
    
    if friend_rel_back:
        db.session.delete(friend_rel_back)
    
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "message": f"已从好友列表中移除 {friend_username}"
    })


from flask import session

@app.route('/submit_guide', methods=['POST'])
def submit_guide():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in first.')
        return redirect(url_for('login'))

    title = request.form.get('title')
    content = request.form.get('content')

    if not title or not content:
        flash('All fields are required.')
        return redirect(url_for('create_guide'))

    if len(title) > 100 or len(content) > 500:
        flash('Title or content too long.')
        return redirect(url_for('create_guide'))

    new_guide = Guides(title=title, content=content, user_id=user_id)
    db.session.add(new_guide)
    db.session.commit()

    flash('Guide created successfully!')
    return redirect(url_for('user_guides', user_id=user_id))


@app.route('/user/<int:user_id>/guides')
def user_guides(user_id):
    session_user_id = session.get('user_id')
    if not session_user_id:
        flash('Please log in first.')
        return redirect(url_for('login'))

    if user_id != session_user_id:
        flash('You can only view your own guides.')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    guides = user.guides.order_by(Guides.created_at.desc()).all()
    return render_template('user_guide.html', user=user, guides=guides)

@app.route('/delete_guide/<int:guide_id>', methods=['POST'])
@login_required
def delete_guide(guide_id):
    guide = Guides.query.get_or_404(guide_id)
    # Check if the guide belongs to the logged-in user
    if guide.user_id != session['user_id']:
        flash('You can only delete your own guides.')
        return redirect(url_for('user_guide'))

    db.session.delete(guide)
    db.session.commit()
    flash('Guide deleted successfully.')
    return redirect(url_for('user_guide'))

if __name__ == '__main__':
    app.run(debug=True)