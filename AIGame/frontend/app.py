from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')

@app.route('/')
def index():
    """前端主页"""
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """提供静态文件"""
    return send_from_directory('static', filename)

if __name__ == '__main__':
    print("🎲 TRPG跑团游戏助手 Frontend v2.0")
    print("正在启动前端服务器...")
    print("前端地址: http://0.0.0.0:3000 (可远程访问)")
    print("请确保后端服务器(0.0.0.0:5000)已启动")
    print("按 Ctrl+C 退出程序")
    
    # 启动Flask应用 - 配置为可远程访问
    app.run(host='0.0.0.0', port=3000, debug=False)
