from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    riot_id = db.Column(db.String(50), nullable=True)
    tagline = db.Column(db.String(50), nullable=True)
    region = db.Column(db.String(20), nullable=True)
    puuid = db.Column(db.String(100), nullable=True)  # 添加了 puuid 字段，以支持 API 功能
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<User {self.username}>'
    

class MatchRecord(db.Model):
    """存储用户对局记录"""
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 修正外键引用
    queue_id = db.Column(db.Integer, nullable=False)
    game_mode = db.Column(db.String(50), nullable=False)
    game_category = db.Column(db.String(50), nullable=False)
    game_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 建立与 User 的关系
    user = db.relationship('User', backref=db.backref('match_records', lazy=True))

    # 建立索引以提高查询性能
    __table_args__ = (
        db.Index('idx_user_match', user_id, match_id),
    )

class GameModeStats(db.Model):
    """存储用户游戏模式统计数据"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)  # 修正外键引用
    sr_5v5_percentage = db.Column(db.Float, default=0)
    aram_percentage = db.Column(db.Float, default=0)
    fun_modes_percentage = db.Column(db.Float, default=0)
    bot_games_percentage = db.Column(db.Float, default=0)
    custom_percentage = db.Column(db.Float, default=0)
    unknown_percentage = db.Column(db.Float, default=0)
    total_matches = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('game_mode_stats', uselist=False))

class Friend(db.Model):
    __tablename__ = 'friends'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 建立与User的关系
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('friends_added', lazy=True))
    friend = db.relationship('User', foreign_keys=[friend_id], backref=db.backref('friends_of', lazy=True))
    
    def __repr__(self):
        return f'<Friend {self.user_id}-{self.friend_id}>'
    
class DetailedAnalysis(db.Model):
    """存储用户详细游戏分析数据"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    
    # 最喜欢的英雄（存储JSON格式）
    favorite_champions = db.Column(db.JSON, default={})
    
    # 最喜欢的位置（存储JSON格式）
    favorite_positions = db.Column(db.JSON, default={})
    
    # 多杀统计
    double_kills = db.Column(db.Integer, default=0)
    triple_kills = db.Column(db.Integer, default=0)
    quadra_kills = db.Column(db.Integer, default=0)
    penta_kills = db.Column(db.Integer, default=0)
    total_multikills = db.Column(db.Integer, default=0)
    avg_multikills_per_match = db.Column(db.Float, default=0)
    
    # 趣味数据
    total_gold_earned = db.Column(db.Integer, default=0)
    avg_gold_per_match = db.Column(db.Integer, default=0)
    total_kills = db.Column(db.Integer, default=0)
    total_deaths = db.Column(db.Integer, default=0)
    total_assists = db.Column(db.Integer, default=0)
    avg_kills_per_match = db.Column(db.Float, default=0)
    avg_deaths_per_match = db.Column(db.Float, default=0)
    avg_assists_per_match = db.Column(db.Float, default=0)
    avg_kda = db.Column(db.Float, default=0)
    total_vision_score = db.Column(db.Integer, default=0)
    avg_vision_score = db.Column(db.Float, default=0)
    total_damage_dealt = db.Column(db.Integer, default=0)
    avg_damage_per_match = db.Column(db.Integer, default=0)
    
    # 敌方英雄和己方英雄数据（存储JSON格式）
    enemy_champions = db.Column(db.JSON, default={})
    ally_champions = db.Column(db.JSON, default={})
    
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    user = db.relationship('User', backref=db.backref('detailed_analysis', uselist=False))