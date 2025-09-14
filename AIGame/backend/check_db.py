#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
import os

def check_database():
    # 确保在正确的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    db_path = "game_data.db"
    
    print(f"🔍 当前目录: {os.getcwd()}")
    print(f"🔍 查找数据库: {os.path.abspath(db_path)}")
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    print(f"📊 检查数据库: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 数据库中的表 ({len(tables)} 个):")
        for table in tables:
            print(f"  - {table}")
        
        # 检查user_sessions表是否存在
        if 'user_sessions' in tables:
            print("✅ user_sessions 表存在")
            
            # 获取表结构
            cursor.execute("PRAGMA table_info(user_sessions);")
            columns = cursor.fetchall()
            print("   表结构:")
            for col in columns:
                print(f"     {col[1]} ({col[2]})")
        else:
            print("❌ user_sessions 表不存在")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查数据库失败: {e}")

if __name__ == "__main__":
    check_database()
