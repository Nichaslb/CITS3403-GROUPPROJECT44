import sqlite3
import os

# 定义数据库路径
DB_PATH = 'users.db'

# 如果数据库文件已经存在，则删除它
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f'已删除现有数据库: {DB_PATH}')

# 连接到数据库（这将创建一个新文件）
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 创建users表
cursor.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    riot_id TEXT,
    tagline TEXT,
    region TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# 提交更改并关闭连接
conn.commit()

# 验证表是否创建成功
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("数据库中的表:")
for table in tables:
    print(f"- {table[0]}")

# 显示users表的结构
cursor.execute("PRAGMA table_info(users);")
columns = cursor.fetchall()
print("\nusers表结构:")
for column in columns:
    print(f"- {column[1]} ({column[2]})")

conn.close()

print(f'\n数据库初始化成功: {DB_PATH}')
print('表 "users" 已创建。')