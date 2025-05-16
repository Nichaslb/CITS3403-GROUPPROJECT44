from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import requests
import time
from functools import wraps
from flask_migrate import Migrate


from models import db, User, GameModeStats, MatchRecord, Friend,DetailedAnalysis
from forms import LoginForm, RegisterForm
from routes.riot_api import fetch_puuid, fetch_rank_info, fetch_match_list, fetch_match_details, get_api_key

app = Flask(__name__, 
           template_folder='template',
           static_url_path='',       # remove URL prefix
           static_folder='.')        # Use the project root directory as the static file directory

app.config['SECRET_KEY'] = os.urandom(24)

# Configure the SQLAlchemy database.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set the Riot API key (if it needs to be retrieved from an environment variable).
app.config['RIOT_API_KEY'] = os.environ.get('RIOT_API_KEY', '')

# Initialize the database.
db.init_app(app)

migrate = Migrate(app, db)

# Make sure all database tables are created before the app starts.
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
        
        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        
        if existing_user:
            flash('username or email already exsit', 'error')
            return render_template('signup.html', form=form)
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )
        
        # If the form has riot_id etc. fields, save this information
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
        
        # query user
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            # update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Login success
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            
            # Set session persistence, if "remember me" is selected, then for 3 days
            if remember:
                session.permanent = True
                app.permanent_session_lifetime = 60 * 60 * 24 * 3  # 3天
            
            # Redirect to the next page or dashboard
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
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/friends')
@login_required
def friends():
    user = User.query.get(session['user_id'])
    return render_template('friends.html', user=user)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    riot_id = request.form.get('riot_id', '')
    tagline = request.form.get('tagline', '')
    region = request.form.get('region', '')
    
    user = User.query.get(session['user_id'])
    
    riot_id_changed = user.riot_id != riot_id
    tagline_changed = user.tagline != tagline
    
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
                flash('Riot account available', 'success')
            elif "error" in result:
                flash(f'Riot info incorrect: {result["error"]}', 'error')
                # 
    
    db.session.commit()
    
    flash('Updated!', 'success')
    return redirect(url_for('profile'))

@app.route('/share')
@login_required
def share():
    return render_template('share.html')

@app.route('/api/puuid')
@login_required
def api_get_puuid():
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({"status": "error", "message": "cannot find userinfo "}), 404
    
 
    if not user.riot_id or not user.tagline:
        return jsonify({
            "status": "error", 
            "message": "Did not set Riot ID or Tagline, please update your profile",
            "needsUpdate": True
        }), 400
    

    api_key = get_api_key()
    if not api_key:
        return jsonify({"status": "error", "message": "Cant fetch api key"}), 500
    
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
    
    # 移除冷却检查代码，直接执行分析
    print(f"开始为用户 {user_id} 分析游戏模式")
    result = analyze_game_modes(user_id)
    print(f"游戏模式分析完成，状态: {result['status']}")
    
    # 如果分析成功，保存详细分析数据到数据库
    if result['status'] == 'success' and 'data' in result and 'detailed_analysis' in result['data']:
        detailed = result['data']['detailed_analysis']
        
        # 查询现有的详细分析数据或创建新记录
        analysis = DetailedAnalysis.query.filter_by(user_id=user_id).first()
        if not analysis:
            analysis = DetailedAnalysis(user_id=user_id)
        
        # 更新详细分析数据
        # 最喜欢的英雄和位置
        analysis.favorite_champions = detailed['favorite_champions']
        analysis.favorite_positions = detailed['favorite_positions']
        
        # 多杀统计
        analysis.double_kills = detailed['multikill_stats']['doubles']
        analysis.triple_kills = detailed['multikill_stats']['triples'] 
        analysis.quadra_kills = detailed['multikill_stats']['quadras']
        analysis.penta_kills = detailed['multikill_stats']['pentas']
        analysis.total_multikills = detailed['multikill_stats']['total']
        analysis.avg_multikills_per_match = detailed['multikill_stats']['average']
        
        # 趣味数据
        analysis.total_gold_earned = detailed['fun_stats']['total_gold_earned']
        analysis.avg_gold_per_match = detailed['fun_stats'].get('avg_gold_per_match', 0)
        analysis.total_kills = detailed['fun_stats']['total_kills']
        analysis.total_deaths = detailed['fun_stats']['total_deaths']
        analysis.total_assists = detailed['fun_stats']['total_assists']
        analysis.avg_kills_per_match = detailed['fun_stats'].get('avg_kills_per_match', 0)
        analysis.avg_deaths_per_match = detailed['fun_stats'].get('avg_deaths_per_match', 0)
        analysis.avg_assists_per_match = detailed['fun_stats'].get('avg_assists_per_match', 0)
        analysis.avg_kda = detailed['fun_stats'].get('avg_kda', 0)
        analysis.total_vision_score = detailed['fun_stats'].get('total_vision_score', 0)
        analysis.avg_vision_score = detailed['fun_stats'].get('avg_vision_score', 0)
        analysis.total_damage_dealt = detailed['fun_stats'].get('total_damage_dealt_to_champions', 0)
        analysis.avg_damage_per_match = detailed['fun_stats'].get('avg_damage_per_match', 0)
        analysis.total_damage_taken = detailed['fun_stats']['total_damage_taken']
        analysis.total_items_purchased = detailed['fun_stats']['total_items_purchased']
        
        # 敌方和己方英雄数据
        if 'enemy_champions' in detailed:
            analysis.enemy_champions = detailed['enemy_champions']
        if 'ally_champions' in detailed:
            analysis.ally_champions = detailed['ally_champions']
        
        analysis.last_updated = datetime.utcnow()
        
        # 保存到数据库
        db.session.add(analysis)
        db.session.commit()
        print(f"已保存用户 {user_id} 的详细分析数据")
    
    return jsonify(result)

def build_simplified_analysis(user_id, matches):
    """
    基于数据库中已有的比赛记录构建简化版的分析数据
    这个函数不会调用Riot API，仅使用已保存的数据
    """
    # 初始化分析数据结构
    analysis = {
        "favorite_champions": {},
        "favorite_positions": {},
        "multikill_stats": {
            "doubles": 0,
            "triples": 0,
            "quadras": 0,
            "pentas": 0,
            "total": 0,
            "average": 0
        },
        "fun_stats": {
            "total_gold_earned": 0,
            "avg_gold_per_match": 0,
            "total_kills": 0,
            "total_deaths": 0,
            "total_assists": 0,
            "avg_kills_per_match": 0,
            "avg_deaths_per_match": 0,
            "avg_assists_per_match": 0,
            "avg_kda": 0,
            "total_vision_score": 0,
            "avg_vision_score": 0,
            "total_damage_dealt_to_champions": 0,
            "avg_damage_per_match": 0
        }
    }
    
    # 尝试查找是否有详细分析数据
    detailed = DetailedAnalysis.query.filter_by(user_id=user_id).first()
    if detailed:
        # 使用数据库中的详细分析数据
        analysis["favorite_champions"] = detailed.favorite_champions
        analysis["favorite_positions"] = detailed.favorite_positions
        analysis["multikill_stats"] = {
            "doubles": detailed.double_kills,
            "triples": detailed.triple_kills,
            "quadras": detailed.quadra_kills,
            "pentas": detailed.penta_kills,
            "total": detailed.total_multikills,
            "average": detailed.avg_multikills_per_match
        }
        analysis["fun_stats"] = {
            "total_gold_earned": detailed.total_gold_earned,
            "avg_gold_per_match": detailed.avg_gold_per_match,
            "total_kills": detailed.total_kills,
            "total_deaths": detailed.total_deaths,
            "total_assists": detailed.total_assists,
            "avg_kills_per_match": detailed.avg_kills_per_match,
            "avg_deaths_per_match": detailed.avg_deaths_per_match,
            "avg_assists_per_match": detailed.avg_assists_per_match,
            "avg_kda": detailed.avg_kda,
            "total_vision_score": detailed.total_vision_score,
            "avg_vision_score": detailed.avg_vision_score,
            "total_damage_dealt_to_champions": detailed.total_damage_dealt,
            "avg_damage_per_match": detailed.avg_damage_per_match,
        }
        
        # 如果有敌方和己方英雄数据，也添加进去
        if hasattr(detailed, 'enemy_champions') and detailed.enemy_champions:
            analysis["enemy_champions"] = detailed.enemy_champions
        if hasattr(detailed, 'ally_champions') and detailed.ally_champions:
            analysis["ally_champions"] = detailed.ally_champions
            
        return analysis
    
    # 如果数据库中没有详细分析，可以返回示例数据
    if not matches or len(matches) == 0:
        # 添加一些示例数据
        popular_champions = {
            "未知英雄": 0
        }
        positions = {
            "未知位置": 0
        }
    else:
        # 尝试从match记录中提取一些基本信息
        # 这里只是一个简化版，无法获取详细的游戏数据
        popular_champions = {"未知英雄": len(matches)}
        positions = {"未知位置": len(matches)}
    
    analysis["favorite_champions"] = popular_champions
    analysis["favorite_positions"] = positions
    
    return analysis

@app.route('/api/game_modes_stats')
@login_required
def api_game_modes_stats():
    """获取当前用户的游戏模式统计数据和详细分析"""
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
    
    # 获取详细分析数据
    detailed_analysis = DetailedAnalysis.query.filter_by(user_id=user_id).first()
    
    # 构建详细分析数据结构
    detailed_data = None
    if detailed_analysis:
        detailed_data = {
            "favorite_champions": detailed_analysis.favorite_champions,
            "favorite_positions": detailed_analysis.favorite_positions,
            "multikill_stats": {
                "doubles": detailed_analysis.double_kills,
                "triples": detailed_analysis.triple_kills,
                "quadras": detailed_analysis.quadra_kills,
                "pentas": detailed_analysis.penta_kills,
                "total": detailed_analysis.total_multikills,
                "average": detailed_analysis.avg_multikills_per_match
            },
            "fun_stats": {
                "total_gold_earned": detailed_analysis.total_gold_earned,
                "avg_gold_per_match": detailed_analysis.avg_gold_per_match,
                "total_kills": detailed_analysis.total_kills,
                "total_deaths": detailed_analysis.total_deaths,
                "total_assists": detailed_analysis.total_assists,
                "avg_kills_per_match": detailed_analysis.avg_kills_per_match,
                "avg_deaths_per_match": detailed_analysis.avg_deaths_per_match,
                "avg_assists_per_match": detailed_analysis.avg_assists_per_match,
                "avg_kda": detailed_analysis.avg_kda,
                "total_vision_score": detailed_analysis.total_vision_score,
                "avg_vision_score": detailed_analysis.avg_vision_score,
                "total_damage_dealt_to_champions": detailed_analysis.total_damage_dealt,
                "avg_damage_per_match": detailed_analysis.avg_damage_per_match,
                "total_damage_taken": detailed_analysis.total_damage_taken,
                "total_items_purchased": detailed_analysis.total_items_purchased
            }
        }
        
        # 如果有敌方和己方英雄数据，也添加进去
        if detailed_analysis.enemy_champions:
            detailed_data["enemy_champions"] = detailed_analysis.enemy_champions
        if detailed_analysis.ally_champions:
            detailed_data["ally_champions"] = detailed_analysis.ally_champions
    else:
        # 如果没有详细分析数据，创建一个简化版的空结构
        detailed_data = build_simplified_analysis(user_id, [])
    
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
                "last_updated": stats.last_updated.strftime("%Y-%m-%d %H:%M:%S"),
                "detailed_analysis": detailed_data
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
            "last_updated": stats.last_updated.strftime("%Y-%m-%d %H:%M:%S"),
            "detailed_analysis": detailed_data
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

@app.route('/api/can_analyze')
@login_required
def api_can_analyze():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"status": "error", "message": "用户未登录"}), 401
    return jsonify({
        "status": "success",
        "canAnalyze": True,
        "message": "可以进行分析"
    })

@app.route('/api/friend_summary/<int:friend_user_id>')
@login_required # Ensure only logged-in users can access
def get_friend_summary(friend_user_id):
    current_user_id = session.get('user_id')

    # Verify if the requested user is actually a friend of the current user.
    # This is an important security/privacy check.
    # Checking both directions of friendship as per your add_friend logic
    is_friend_check = Friend.query.filter(
        Friend.user_id == current_user_id,
        Friend.friend_id == friend_user_id
    ).first()

    if not is_friend_check:
        # If you want to be more discreet and not reveal friendship status,
        # you could return a generic "data not found" or "permission denied"
        return jsonify({"status": "error", "message": "Requested user is not a friend or permission denied."}), 403

    friend_user = User.query.get(friend_user_id)
    if not friend_user:
        return jsonify({"status": "error", "message": "Friend user not found."}), 404

    detailed_analysis = DetailedAnalysis.query.filter_by(user_id=friend_user_id).first()
    game_mode_stats = GameModeStats.query.filter_by(user_id=friend_user_id).first()

    if not detailed_analysis or not game_mode_stats:
        return jsonify({
            "status": "info",
            "message": f"Analysis data for {friend_user.username} is not available yet. They might need to perform an analysis on their dashboard.",
            "data": {
                "username": friend_user.username,
                "favorite_champions": [],
                "total_multikills": 0,
                "favorite_game_mode": "Not Available"
            }
        }), 200 # Using 200 with an info message as data structure is still returned

    summary_data = {
        "username": friend_user.username,
        "favorite_champions": [],
        "total_multikills": 0,
        "favorite_game_mode": "Not Available"
    }

    # 1. Extract Favorite Champions (e.g., top 3)
    if detailed_analysis.favorite_champions:
        # Assuming favorite_champions is a dict like {'ChampionName': play_count}
        # Sort by play_count and take top 3 champion names
        try:
            sorted_champions = sorted(detailed_analysis.favorite_champions.items(), key=lambda item: item[1], reverse=True)
            summary_data["favorite_champions"] = [champ[0] for champ in sorted_champions[:3]]
        except Exception as e:
            print(f"Error processing favorite champions for user {friend_user_id}: {e}")
            summary_data["favorite_champions"] = ["Error processing"]


    # 2. Calculate Total Multikills
    summary_data["total_multikills"] = (
        (detailed_analysis.double_kills or 0) +
        (detailed_analysis.triple_kills or 0) +
        (detailed_analysis.quadra_kills or 0) +
        (detailed_analysis.penta_kills or 0)
    )

    # 3. Determine Favorite Game Mode
    if game_mode_stats:
        modes_percentages = {
            "Summoner's Rift 5v5": game_mode_stats.sr_5v5_percentage or 0,
            "ARAM": game_mode_stats.aram_percentage or 0,
            "Fun Modes": game_mode_stats.fun_modes_percentage or 0,
            "Bot Games": game_mode_stats.bot_games_percentage or 0,
            "Custom Games": game_mode_stats.custom_percentage or 0,
        }
        # Filter out modes with 0% and find the max
        played_modes = {mode: perc for mode, perc in modes_percentages.items() if perc > 0}
        if played_modes:
            summary_data["favorite_game_mode"] = max(played_modes, key=played_modes.get)
        elif game_mode_stats.total_matches > 0 : # If analyzed but no specific mode preference
             summary_data["favorite_game_mode"] = "Varied / Other Modes"
        else: # No matches analyzed or all percentages are 0
            summary_data["favorite_game_mode"] = "N/A (No games analyzed)"


    return jsonify({
        "status": "success",
        "data": summary_data
    })

if __name__ == '__main__':
    app.run(debug=True)