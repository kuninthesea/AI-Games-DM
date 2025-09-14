# -*- coding: utf-8 -*-
"""
服务器启动脚本 - 用于远程部署
只启动服务，不打开浏览器
"""
import subprocess
import sys
import os
import time
import socket
import json

def check_port(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False  # 端口未被占用
        except OSError:
            return True   # 端口已被占用

def get_local_ip():
    """获取本机IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def install_requirements():
    """安装必要的依赖"""
    print("🔧 检查并安装依赖...")
    try:
        import flask
        import openai
        import sqlite3
        print("✅ 依赖已安装")
    except ImportError:
        print("📦 正在安装依赖...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "openai", "google-generativeai"])
        print("✅ 依赖安装完成")

def init_database():
    """初始化分离数据库系统"""
    print("📋 初始化分离数据库系统...")
    try:
        # 导入数据库分离管理器
        backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        from database_separation import db_separation_manager
        
        # 删除旧数据库文件以重新创建
        #game_db = os.path.join(backend_path, 'game_data.db')
        world_db = os.path.join(backend_path, 'world_data.db')
        # if os.path.exists(game_db):
        #     os.remove(game_db)
        #     print("🗑️ 删除旧的游戏数据库")
        if os.path.exists(world_db):
            os.remove(world_db)
            print("🗑️ 删除旧的世界数据库")
        
        # 初始化分离数据库
        db_separation_manager.init_databases()
        print("✅ 分离数据库系统初始化成功")
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False

def start_backend():
    """启动后端服务"""
    if check_port(5000):
        print("✅ 后端服务已在运行 (端口5000)")
        return True
    print("🚀 启动后端服务...")
    os.chdir("backend")
    process = subprocess.Popen([sys.executable, "app.py"])
    os.chdir("..")
    return False

def start_frontend():
    """启动前端服务"""
    if check_port(3000):
        print("✅ 前端服务已在运行 (端口3000)")
        return True
    print("🌐 启动前端服务...")
    os.chdir("frontend")
    process = subprocess.Popen([sys.executable, "app.py"])
    os.chdir("..")
    return False

def main():
    print("🎲 TRPG跑团游戏助手 - 服务器版本")
    print("=" * 50)
    
    # 检查当前目录
    if not os.path.exists("backend") or not os.path.exists("frontend"):
        print("❌ 错误：请在项目根目录运行此脚本")
        return 1
    
    try:
        # 安装依赖
        install_requirements()
        
        # 初始化数据库
        init_database()
        
        # 启动后端
        backend_was_running = start_backend()
        if not backend_was_running:
            time.sleep(3)
        
        # 启动前端
        frontend_was_running = start_frontend()
        if not frontend_was_running:
            time.sleep(3)
        
        # 获取本机IP地址
        local_ip = get_local_ip()
        
        print("\n✅ 服务器启动完成！")
        print("=" * 60)
        print("🌐 访问地址:")
        print(f"🔗 游戏前端: http://{local_ip}:3000")
        print(f"🔗 API后端: http://{local_ip}:5000")
        print("\n📊 数据库: SQLite (自动创建)")
        print("=" * 60)
        print("\n💡 使用说明:")
        print("• 用户访问游戏: http://{your-server-ip}:3000")
        print("• 首次使用请先注册账号")
        print("• 确保防火墙允许端口3000和5000的访问")
        print("• 服务已在后台运行")
        print("\n⚠️  要停止服务，请使用 Ctrl+C 或关闭相应进程")
        
        # 保持脚本运行
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n🛑 收到停止信号，服务器将继续在后台运行")
            print("如需完全停止，请手动终止相关进程")
        
        return 0
        
    except Exception as e:
        print("❌ 启动失败: " + str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())
