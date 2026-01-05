from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime
from itertools import groupby
from env import ADMIN_PASSWORD  
app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect('blog.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS posts 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT NOT NULL, 
                  content TEXT NOT NULL, 
                  created_at TEXT NOT NULL)''')
    conn.close()

@app.route('/')
def index():
    # 允许通过 URL 参数切换模式： /?mode=year 或 /?mode=month
    mode = request.args.get('mode', 'month') 
    
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY created_at DESC').fetchall()
    conn.close()

    # 将行对象转换为字典列表，方便处理
    post_list = [dict(post) for post in posts]

    # 根据模式确定分组的切片长度：'2024-05' (7位) 或 '2024' (4位)
    slice_end = 7 if mode == 'month' else 4
    
    # 进行分组
    grouped_posts = []
    for key, group in groupby(post_list, lambda x: x['created_at'][:slice_end]):
        grouped_posts.append({
            'period': key,
            'posts': list(group)
        })

    return render_template('index.html', posts=posts, grouped_posts=grouped_posts, mode=mode)

@app.route('/post/<int:post_id>')
def post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    conn.close()
    return render_template('post.html', post=post)

@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        input_pwd = request.form.get('password') # 获取用户输入的密码

        if input_pwd != ADMIN_PASSWORD:
            return "密码错误，拒绝发布！", 403

        created_at = datetime.now().strftime('%Y-%m-%d %H:%M')
        conn = get_db_connection()
        conn.execute('INSERT INTO posts (title, content, created_at) VALUES (?, ?, ?)',
                     (title, content, created_at))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('create.html')

# 添加删除功能，方便管理
@app.route('/post/<int:post_id>/delete', methods=('POST',))
def delete(post_id):
    input_pwd = request.form.get('password') # 从删除表单中获取

    if input_pwd != ADMIN_PASSWORD:
        return "密码错误，无法删除！", 403

    conn = get_db_connection()
    conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)