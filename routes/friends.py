# routes/friends.py
from flask import jsonify, request, session
from datetime import datetime
from models import db, User

# 新增一个Friend模型
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

# 添加用户最后登录时间字段
# 需要在User模型中添加last_login字段
# 在models.py中的User类中添加: last_login = db.Column(db.DateTime)
# 并在login函数中更新last_login: user.last_login = datetime.utcnow()

# 搜索用户
def search_user(username, exact=False):
    """
    通过用户名搜索用户
    params:
        username: 要搜索的用户名
        exact: 是否为精确匹配
    """
    current_user_id = session.get('user_id')
    
    if exact:
        # 精确匹配
        users = User.query.filter(
            User.id != current_user_id,
            User.username == username
        ).all()
    else:
        # 模糊匹配
        users = User.query.filter(
            User.id != current_user_id,
            User.username.like(f'%{username}%')
        ).all()
    
    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "username": user.username,
            "riot_id": user.riot_id,
            "tagline": user.tagline,
            "region": user.region
        })
    
    return user_list

# 获取好友列表
def get_friends():
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
    
    return friend_list

# 添加好友
def add_friend(friend_id):
    """添加好友关系"""
    current_user_id = session.get('user_id')
    
    # 检查是否已经是好友
    existing = Friend.query.filter_by(
        user_id=current_user_id, 
        friend_id=friend_id
    ).first()
    
    if existing:
        return {"status": "error", "message": "已经是好友"}
    
    # 检查用户是否存在
    friend = User.query.get(friend_id)
    if not friend:
        return {"status": "error", "message": "用户不存在"}
    
    # 添加好友关系
    new_friend = Friend(user_id=current_user_id, friend_id=friend_id)
    db.session.add(new_friend)
    
    # 互相添加（可选）
    new_friend_back = Friend(user_id=friend_id, friend_id=current_user_id)
    db.session.add(new_friend_back)
    
    db.session.commit()
    
    return {
        "status": "success",
        "message": f"已添加 {friend.username} 为好友"
    }

# 删除好友
def remove_friend(friend_id):
    """删除好友关系"""
    current_user_id = session.get('user_id')
    
    # 查找好友关系
    friend_rel = Friend.query.filter_by(
        user_id=current_user_id, 
        friend_id=friend_id
    ).first()
    
    if not friend_rel:
        return {"status": "error", "message": "好友关系不存在"}
    
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
    
    return {
        "status": "success",
        "message": f"已从好友列表中移除 {friend_username}"
    }