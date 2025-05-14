import requests
import time
import os
from flask import jsonify, current_app
from datetime import datetime
from models import db, User, GameModeStats, MatchRecord  # 假设你已经有User模型

# 游戏模式映射
GAME_MODE_MAPPING = {
    # 常规5v5
    400: "Normal Draft",     # 匹配模式
    420: "Ranked Solo/Duo",  # 单双排
    430: "Normal Blind",     # 匹配模式盲选
    440: "Ranked Flex",      # 灵活排位
    
    # ARAM
    450: "ARAM",             # 极地大乱斗
    
    # 娱乐模式
    700: "Clash",            # 冠军杯
    720: "ARAM Clash",       # 极地大乱斗冠军杯
    830: "Co-op vs AI",      # 人机
    840: "Co-op vs AI",      # 人机
    850: "Co-op vs AI",      # 人机
    900: "URF",              # 无限火力
    1020: "One for All",     # 克隆模式
    1300: "Nexus Blitz",     # 闪击模式
    1400: "Ultimate Spellbook", # 终极魔典
    1700: "Arena",           # 竞技场
    1900: "URF",             # 无限火力
    
    # 其他
    0: "Custom Game"         # 自定义游戏
}

# 游戏模式类别
MODE_CATEGORIES = {
    'SR_5v5': [400, 420, 430, 440],         # 常规5v5
    'ARAM': [450, 720],                     # 极地大乱斗
    'Fun_Modes': [700, 900, 1020, 1300, 1400, 1700, 1900],  # 娱乐模式
    'Bot_Games': [830, 840, 850],           # 人机模式
    'Custom': [0]                           # 自定义
}

# 反向映射以根据queueId获取类别
QUEUE_TO_CATEGORY = {}
for category, queue_ids in MODE_CATEGORIES.items():
    for queue_id in queue_ids:
        QUEUE_TO_CATEGORY[queue_id] = category

# API 区域映射
REGION_ROUTING = {
    'na': 'americas',
    'kr': 'asia',
    'jp': 'asia',
    'euw': 'europe',
    'eune': 'europe',
    'tr': 'europe',
    'ru': 'europe',
    'br': 'americas',
    'lan': 'americas',
    'las': 'americas',
    'oce': 'sea',
    'ph': 'sea',
    'sg': 'sea',
    'th': 'sea',
    'tw': 'asia',
    'vn': 'sea'
}

def get_api_key():
    """从环境变量或Flask配置获取Riot API密钥"""
    from routes.riot_api import get_api_key as riot_get_api_key
    
    # 尝试使用riot_api.py中的方法获取
    api_key = riot_get_api_key()
    
    # 如果上面的方法失败，尝试从环境变量或配置获取
    if not api_key:
        api_key = os.environ.get('RIOT_API_KEY')
        
        if not api_key and current_app:
            api_key = current_app.config.get('RIOT_API_KEY')
    
    # 如果仍未获取到有效密钥，记录详细日志
    if not api_key:
        print("警告：无法获取有效的Riot API密钥")
    else:
        print(f"成功获取API密钥: {api_key[:5]}...")
    
    return api_key

def get_routing_value(region):
    """根据用户的区域确定API路由值"""
    region = region.lower()
    return REGION_ROUTING.get(region, 'sea')  # 默认使用sea

def fetch_match_history(user_id):
    """获取用户最近30场对局的历史并分析游戏模式分布"""
    # 获取用户信息
    user = User.query.get(user_id)
    if not user or not user.puuid:
        print(f"用户ID {user_id} 未找到或未设置PUUID")
        return {"status": "error", "message": "用户未找到或未设置PUUID"}
    
    # 获取API密钥
    api_key = get_api_key()
    if not api_key:
        print("无法获取API密钥")
        return {"status": "error", "message": "无法获取API密钥"}
    
    # 根据用户区域确定API路由
    routing_value = get_routing_value(user.region)
    print(f"用户 {user.username} (ID: {user_id}) 开始获取最近30场对局，区域: {user.region}, 路由: {routing_value}")
    
    # 获取最近30场对局IDs
    match_list_url = f"https://{routing_value}.api.riotgames.com/lol/match/v5/matches/by-puuid/{user.puuid}/ids?start=0&count=30"
    headers = {"X-Riot-Token": api_key}
    
    try:
        response = requests.get(match_list_url, headers=headers)
        response.raise_for_status()
        match_ids = response.json()
        print(f"成功获取 {len(match_ids)} 场对局ID: {match_ids[:3]}... (仅显示前3个)")
    except requests.exceptions.RequestException as e:
        print(f"获取对局ID列表失败: {str(e)}")
        return {"status": "error", "message": f"获取对局ID列表失败: {str(e)}"}
    
    # 初始化游戏模式计数
    mode_counts = {
        'SR_5v5': 0,
        'ARAM': 0,
        'Fun_Modes': 0,
        'Bot_Games': 0,
        'Custom': 0,
        'Unknown': 0
    }
    
    # 遍历每个对局
    processed_matches = []
    success_count = 0
    db_count = 0
    api_count = 0
    
    for index, match_id in enumerate(match_ids):
        # 检查数据库中是否已存在此对局记录
        existing_match = MatchRecord.query.filter_by(match_id=match_id, user_id=user_id).first()
        
        if existing_match:
            # 如果已存在，直接使用数据库中的信息
            category = existing_match.game_category
            mode_counts[category] += 1
            processed_matches.append({
                "match_id": match_id,
                "queue_id": existing_match.queue_id,
                "game_mode": existing_match.game_mode,
                "category": category,
                "date": existing_match.game_date.strftime("%Y-%m-%d %H:%M:%S")
            })
            db_count += 1
            success_count += 1
            print(f"[{index+1}/30] 对局 {match_id} 已从数据库获取")
        else:
            # 获取对局详情
            match_detail_url = f"https://{routing_value}.api.riotgames.com/lol/match/v5/matches/{match_id}"
            
            try:
                print(f"[{index+1}/30] 正在从Riot API获取对局 {match_id} 详情...")
                match_response = requests.get(match_detail_url, headers=headers)
                match_response.raise_for_status()
                match_data = match_response.json()
                
                # 提取游戏模式信息
                queue_id = match_data.get('info', {}).get('queueId', 0)
                game_mode = GAME_MODE_MAPPING.get(queue_id, "Unknown")
                category = QUEUE_TO_CATEGORY.get(queue_id, "Unknown")
                game_creation = match_data.get('info', {}).get('gameCreation', 0)
                game_date = datetime.fromtimestamp(game_creation / 1000)
                
                # 增加计数
                mode_counts[category] += 1
                
                # 存储对局信息到数据库
                new_match = MatchRecord(
                    match_id=match_id,
                    user_id=user_id,
                    queue_id=queue_id,
                    game_mode=game_mode,
                    game_category=category,
                    game_date=game_date
                )
                db.session.add(new_match)
                
                processed_matches.append({
                    "match_id": match_id,
                    "queue_id": queue_id,
                    "game_mode": game_mode,
                    "category": category,
                    "date": game_date.strftime("%Y-%m-%d %H:%M:%S")
                })
                
                api_count += 1
                success_count += 1
                print(f"[{index+1}/30] 对局 {match_id} 已成功从API获取并创建记录，游戏模式: {game_mode}")
                
                # 避免API速率限制
                time.sleep(1.2)  # Riot API 限制是每分钟 100 请求，保守估计
                
            except requests.exceptions.RequestException as e:
                # 记录错误但继续处理其他对局
                print(f"[{index+1}/30] 获取对局 {match_id} 详情失败: {str(e)}")
                continue
    
    # 提交所有数据库更改
    db.session.commit()
    print(f"已提交所有数据库更改，成功处理 {success_count}/30 场对局（{db_count}场从数据库获取，{api_count}场从API获取）")
    
    # 计算百分比
    total_matches = len(processed_matches)
    mode_percentages = {}
    for mode, count in mode_counts.items():
        if total_matches > 0:
            percentage = round((count / total_matches) * 100, 2)
        else:
            percentage = 0
        mode_percentages[mode] = percentage
    
    # 更新或创建用户的游戏模式统计
    stats = GameModeStats.query.filter_by(user_id=user_id).first()
    if not stats:
        stats = GameModeStats(user_id=user_id)
        print(f"为用户 {user_id} 创建新的游戏模式统计记录")
    else:
        print(f"更新用户 {user_id} 的游戏模式统计记录")
    
    # 更新统计信息
    stats.sr_5v5_percentage = mode_percentages['SR_5v5']
    stats.aram_percentage = mode_percentages['ARAM']
    stats.fun_modes_percentage = mode_percentages['Fun_Modes']
    stats.bot_games_percentage = mode_percentages['Bot_Games']
    stats.custom_percentage = mode_percentages['Custom']
    stats.unknown_percentage = mode_percentages['Unknown']
    stats.total_matches = total_matches
    stats.last_updated = datetime.now()
    
    db.session.add(stats)
    db.session.commit()
    print(f"已更新游戏模式统计：常规5v5 {mode_percentages['SR_5v5']}%, ARAM {mode_percentages['ARAM']}%, 娱乐模式 {mode_percentages['Fun_Modes']}%")
    
    return {
        "status": "success",
        "data": {
            "mode_counts": mode_counts,
            "mode_percentages": mode_percentages,
            "total_matches": total_matches,
            "matches": processed_matches
        }
    }

def analyze_game_modes(user_id):
    """分析用户最近30场对局的游戏模式分布"""
    result = fetch_match_history(user_id)
    
    if result["status"] == "error":
        return result
    
    # 可以在这里添加更多分析逻辑
    return result