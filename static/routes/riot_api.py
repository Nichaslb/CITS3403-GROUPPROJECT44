import requests
import os
from flask import current_app
import urllib.parse

# 获取API KEY
def get_api_key():
    try:
        # 从GitHub Gist获取API KEY
        response = requests.get("https://gist.githubusercontent.com/Choukaretsu/1e1676e2b1ac3acfad4553686f5db66c/raw")
        if response.status_code == 200:
            api_key = response.text.strip()
            return api_key
        else:
            current_app.logger.error(f"无法获取API KEY，状态码: {response.status_code}")
            return None
    except Exception as e:
        current_app.logger.error(f"获取API KEY出错: {str(e)}")
        return None

# 获取Riot API请求头
def get_riot_headers(api_key):
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://developer.riotgames.com",
        "X-Riot-Token": api_key
    }

# 获取玩家PUUID
def fetch_puuid(game_name, tag_line, api_key=None):
    if not api_key:
        api_key = get_api_key()
        if not api_key:
            return {"error": "无法获取API密钥"}
    
    # URL编码游戏名和标签
    encoded_game_name = urllib.parse.quote(game_name)
    encoded_tag_line = urllib.parse.quote(tag_line)
    
    url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{encoded_game_name}/{encoded_tag_line}"
    
    try:
        response = requests.get(url, headers=get_riot_headers(api_key))
        if response.status_code == 200:
            account_data = response.json()
            current_app.logger.info(f"成功获取PUUID: {account_data['puuid']}，用户: {game_name}#{tag_line}")
            return {
                "puuid": account_data["puuid"],
                "gameName": account_data["gameName"],
                "tagLine": account_data["tagLine"]
            }
        else:
            error_msg = f"PUUID请求失败，状态码: {response.status_code}"
            if response.status_code == 404:
                error_msg = f"找不到玩家 {game_name}#{tag_line}"
            elif response.status_code == 401:
                error_msg = "API密钥无效或已过期"
            
            current_app.logger.error(error_msg)
            return {"error": error_msg}
    except Exception as e:
        current_app.logger.error(f"获取PUUID出错: {str(e)}")
        return {"error": f"获取PUUID出错: {str(e)}"}

# 获取段位信息
def fetch_rank_info(puuid, api_key=None):
    if not api_key:
        api_key = get_api_key()
        if not api_key:
            return {"error": "无法获取API密钥"}
    
    url = f"https://oc1.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
    try:
        response = requests.get(url, headers=get_riot_headers(api_key))
        if response.status_code == 200:
            return response.json()
        else:
            current_app.logger.error(f"段位请求失败，状态码: {response.status_code}")
            return {"error": f"段位请求失败，状态码: {response.status_code}"}
    except Exception as e:
        current_app.logger.error(f"获取段位信息出错: {str(e)}")
        return {"error": f"获取段位信息出错: {str(e)}"}

# 获取比赛ID列表
def fetch_match_list(puuid, count=20, api_key=None):
    if not api_key:
        api_key = get_api_key()
        if not api_key:
            return {"error": "无法获取API密钥"}
    
    url = f"https://sea.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"
    try:
        response = requests.get(url, headers=get_riot_headers(api_key))
        if response.status_code == 200:
            return response.json()
        else:
            current_app.logger.error(f"比赛ID请求失败，状态码: {response.status_code}")
            return {"error": f"比赛ID请求失败，状态码: {response.status_code}"}
    except Exception as e:
        current_app.logger.error(f"获取比赛ID列表出错: {str(e)}")
        return {"error": f"获取比赛ID列表出错: {str(e)}"}

# 获取比赛详情
def fetch_match_details(match_id, api_key=None):
    if not api_key:
        api_key = get_api_key()
        if not api_key:
            return {"error": "无法获取API密钥"}
    
    url = f"https://sea.api.riotgames.com/lol/match/v5/matches/{match_id}"
    try:
        response = requests.get(url, headers=get_riot_headers(api_key))
        if response.status_code == 200:
            return response.json()
        else:
            current_app.logger.error(f"比赛详情请求失败，状态码: {response.status_code}")
            return {"error": f"比赛详情请求失败，状态码: {response.status_code}"}
    except Exception as e:
        current_app.logger.error(f"获取比赛详情出错: {str(e)}")
        return {"error": f"获取比赛详情出错: {str(e)}"}