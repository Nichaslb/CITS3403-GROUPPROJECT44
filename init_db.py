import sqlite3
import os

# 定义数据库路径
DB_PATH = 'users.db'

# 如果数据库文件已经存在，则删除它
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"Removed existing database: {DB_PATH}")

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
conn.close()

print(f"Database initialized successfully: {DB_PATH}")
print("Table 'users' created.")