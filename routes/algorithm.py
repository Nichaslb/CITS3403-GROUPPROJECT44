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
    """分析用户最近30场对局的游戏模式分布和详细统计数据"""
    print(f"开始为用户 {user_id} 分析游戏模式和详细统计...")
    # 基本的游戏模式分析
    result = fetch_match_history(user_id)
    
    if result["status"] == "error":
        print(f"分析失败，错误信息: {result['message']}")
        return result
    
    # 获取用户PUUID用于识别用户在对局中的数据
    user = User.query.get(user_id)
    if not user or not user.puuid:
        print(f"无法获取用户 {user_id} 的PUUID")
        return {"status": "error", "message": "无法获取用户PUUID"}
    
    user_puuid = user.puuid
    print(f"获取到用户 {user.username} 的PUUID: {user_puuid[:8]}...")
    
    # 获取API密钥
    api_key = get_api_key()
    if not api_key:
        print("无法获取API密钥，终止详细分析")
        return {"status": "error", "message": "无法获取API密钥"}
    
    # 获取路由值
    routing_value = get_routing_value(user.region)
    print(f"使用区域路由: {routing_value}")
    
    # 分析结果初始化
    analysis_result = {
        "favorite_champions": {},  # 最喜欢的英雄
        "favorite_positions": {},  # 最喜欢的位置
        "enemy_champions": {},     # 敌方出现最多的英雄
        "ally_champions": {},      # 我方出现最多的英雄
        "multikill_stats": {       # 多杀统计
            "total": 0,
            "average": 0,
            "doubles": 0,
            "triples": 0,
            "quadras": 0,
            "pentas": 0
        },
        "fun_stats": {             # 趣味数据
            "total_gold_earned": 0,
            "total_kills": 0,
            "total_damage_taken": 0,
            "total_items_purchased": 0,
            "total_deaths": 0,
            "total_assists": 0,
            "total_vision_score": 0,
            "total_time_played": 0,
            "total_damage_dealt_to_champions": 0
        }
    }
    
    # 获取对局ID列表
    processed_matches = result["data"]["matches"]
    print(f"准备分析 {len(processed_matches)} 场比赛的详细数据...")
    
    # 计数变量
    match_count = 0
    sr_match_count = 0  # 召唤师峡谷对局计数(5v5)
    
    # 遍历每个对局进行详细分析
    for match_data in processed_matches:
        match_id = match_data["match_id"]
        
        # 获取对局详情（如果不是从API直接获取的）
        try:
            # 需要从API获取完整对局详情
            match_detail_url = f"https://{routing_value}.api.riotgames.com/lol/match/v5/matches/{match_id}"
            headers = {"X-Riot-Token": api_key}
            
            print(f"正在获取对局 {match_id} 的详细信息以进行分析...")
            match_response = requests.get(match_detail_url, headers=headers)
            match_response.raise_for_status()
            match_detail_data = match_response.json()
            
            # 找到用户在这场对局中的数据
            user_data = None
            team_id = None
            for participant in match_detail_data.get('info', {}).get('participants', []):
                if participant.get('puuid') == user_puuid:
                    user_data = participant
                    team_id = participant.get('teamId')
                    break
            
            if not user_data:
                print(f"未找到用户在对局 {match_id} 中的数据，跳过")
                continue
            
            # 增加计数
            match_count += 1
            
            # 1. 收集最喜欢的英雄数据
            champion_name = user_data.get('championName', 'Unknown')
            analysis_result["favorite_champions"][champion_name] = analysis_result["favorite_champions"].get(champion_name, 0) + 1
            print(f"添加英雄数据: {champion_name}")
            
            # 2. 收集最喜欢的位置数据
            position = user_data.get('individualPosition', '')
            if position and position != 'Invalid':
                analysis_result["favorite_positions"][position] = analysis_result["favorite_positions"].get(position, 0) + 1
                print(f"添加位置数据: {position}")
            
            # 3. 收集多杀统计
            doubles = user_data.get('doubleKills', 0)
            triples = user_data.get('tripleKills', 0)
            quadras = user_data.get('quadraKills', 0)
            pentas = user_data.get('pentaKills', 0)
            
            analysis_result["multikill_stats"]["doubles"] += doubles
            analysis_result["multikill_stats"]["triples"] += triples 
            analysis_result["multikill_stats"]["quadras"] += quadras
            analysis_result["multikill_stats"]["pentas"] += pentas
            
            multikills_this_match = doubles + triples + quadras + pentas
            analysis_result["multikill_stats"]["total"] += multikills_this_match
            print(f"添加多杀数据: 双杀 {doubles}, 三杀 {triples}, 四杀 {quadras}, 五杀 {pentas}")
            
            # 4. 收集趣味数据
            gold_earned = user_data.get('goldEarned', 0)
            kills = user_data.get('kills', 0)
            deaths = user_data.get('deaths', 0)
            assists = user_data.get('assists', 0)
            damage_taken = user_data.get('totalDamageTaken', 0)
            items_purchased = user_data.get('itemsPurchased', 0)
            vision_score = user_data.get('visionScore', 0)  # 添加这行
            damage_dealt = user_data.get('totalDamageDealtToChampions', 0)  # 添加这行
            time_played = match_detail_data.get('info', {}).get('gameDuration', 0)  # 添加这行

            print(f"收集数据: 视野得分 {vision_score}, 游戏时长 {time_played}, 造成伤害 {damage_dealt}")
            print(f"收集数据: 承受伤害 {damage_taken}, 购买装备数 {items_purchased}")

            # 确保所有数值都为整数类型
            analysis_result["fun_stats"]["total_gold_earned"] += int(gold_earned)
            analysis_result["fun_stats"]["total_kills"] += int(kills)
            analysis_result["fun_stats"]["total_deaths"] += int(deaths)
            analysis_result["fun_stats"]["total_assists"] += int(assists)
            analysis_result["fun_stats"]["total_damage_taken"] += int(damage_taken)
            analysis_result["fun_stats"]["total_items_purchased"] += int(items_purchased)
            analysis_result["fun_stats"]["total_vision_score"] += int(vision_score)  # 修改这行
            analysis_result["fun_stats"]["total_time_played"] += int(time_played)  # 修改这行
            analysis_result["fun_stats"]["total_damage_dealt_to_champions"] += int(damage_dealt)  # 修改这行

            print(f"添加趣味数据: 金币 {gold_earned}, KDA {kills}/{deaths}/{assists}")
            
            # 5. 只为5v5对局收集队友和敌人信息
            queue_id = match_detail_data.get('info', {}).get('queueId', 0)
            if queue_id in MODE_CATEGORIES['SR_5v5'] or queue_id in MODE_CATEGORIES['ARAM']:  # 支持 5v5 和 ARAM 模式
                if queue_id in MODE_CATEGORIES['SR_5v5']:
                    sr_match_count += 1  # 统计 5v5 对局数量

                # 收集我方和敌方英雄数据
                for participant in match_detail_data.get('info', {}).get('participants', []):
                    participant_team_id = participant.get('teamId')
                    participant_champion = participant.get('championName', 'Unknown')

                    # 排除玩家自己
                    if participant.get('puuid') != user_puuid:
                        if participant_team_id == team_id:  # 队友
                            analysis_result["ally_champions"][participant_champion] = analysis_result["ally_champions"].get(participant_champion, 0) + 1
                        else:  # 敌人
                            analysis_result["enemy_champions"][participant_champion] = analysis_result["enemy_champions"].get(participant_champion, 0) + 1
            
            # 防止API速率限制
            time.sleep(1.2)
            
        except requests.exceptions.RequestException as e:
            print(f"获取对局 {match_id} 详情失败: {str(e)}")
            continue
    
    # 计算平均每局多杀次数
    if match_count > 0:
        analysis_result["multikill_stats"]["average"] = round(analysis_result["multikill_stats"]["total"] / match_count, 2)
    
    print(f"整理分析数据，处理了 {match_count} 场比赛...")
    
    # 按出现次数排序各数据
    analysis_result["favorite_champions"] = dict(sorted(analysis_result["favorite_champions"].items(), key=lambda x: x[1], reverse=True))
    analysis_result["favorite_positions"] = dict(sorted(analysis_result["favorite_positions"].items(), key=lambda x: x[1], reverse=True))
    
    # 仅当有5v5对局时才排序敌我英雄数据
    if sr_match_count > 0:
        analysis_result["enemy_champions"] = dict(sorted(analysis_result["enemy_champions"].items(), key=lambda x: x[1], reverse=True))
        analysis_result["ally_champions"] = dict(sorted(analysis_result["ally_champions"].items(), key=lambda x: x[1], reverse=True))
    
    # 添加平均值到趣味数据
    if match_count > 0:
        analysis_result["fun_stats"]["avg_gold_per_match"] = round(analysis_result["fun_stats"]["total_gold_earned"] / match_count)
        analysis_result["fun_stats"]["avg_kills_per_match"] = round(analysis_result["fun_stats"]["total_kills"] / match_count, 1)
        analysis_result["fun_stats"]["avg_deaths_per_match"] = round(analysis_result["fun_stats"]["total_deaths"] / match_count, 1)
        analysis_result["fun_stats"]["avg_assists_per_match"] = round(analysis_result["fun_stats"]["total_assists"] / match_count, 1)
        analysis_result["fun_stats"]["avg_kda"] = round((analysis_result["fun_stats"]["total_kills"] + analysis_result["fun_stats"]["total_assists"]) / 
                                                      max(analysis_result["fun_stats"]["total_deaths"], 1), 2)
        analysis_result["fun_stats"]["avg_vision_score"] = round(analysis_result["fun_stats"]["total_vision_score"] / match_count, 1)
        analysis_result["fun_stats"]["avg_damage_per_match"] = round(analysis_result["fun_stats"]["total_damage_dealt_to_champions"] / match_count)
    
    # 将分析结果添加到返回数据中
    result["data"]["detailed_analysis"] = analysis_result
    
    print(f"分析完成，成功处理 {match_count} 场对局的详细数据")
    print(f"详细分析结果: {analysis_result}")
    
    return result