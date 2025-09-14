# -*- coding: utf-8 -*-
from datetime import datetime
from database import DatabaseManager
from database_separation import db_separation_manager


class HistoryManager:
    def __init__(self):
        self.db = db_separation_manager

    def save_message(self, username, character, role, content):
        """保存聊天消息到数据库"""
        try:
            self.db.execute_query(
                "INSERT INTO chat_history (username, character, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
                (username, character, role, content, datetime.now().isoformat())
            )
            return True
        except Exception as e:
            print(f"保存消息出错: {e}")
            return False

    def get_character_history(self, username, character, limit=50):
        """获取指定角色的聊天历史"""
        try:
            messages = self.db.execute_query(
                "SELECT role, content, timestamp FROM chat_history WHERE username = ? AND character = ? ORDER BY timestamp DESC LIMIT ?",
                (username, character, limit), fetch_all=True
            )
            
            # 格式化消息
            formatted_messages = []
            for msg in reversed(messages):  # 按时间正序排列
                formatted_messages.append({
                    'role': msg['role'],
                    'content': msg['content'],
                    'timestamp': msg['timestamp']
                })
            
            return formatted_messages
        except Exception as e:
            print(f"获取聊天历史出错: {e}")
            return []

    def get_all_characters(self, username):
        """获取用户的所有聊天角色"""
        try:
            characters = self.db.execute_query(
                "SELECT DISTINCT character FROM chat_history WHERE username = ? ORDER BY character",
                (username,), fetch_all=True
            )
            
            return [char['character'] for char in characters]
        except Exception as e:
            print(f"获取角色列表出错: {e}")
            return []

    def clear_character_history(self, username, character):
        """清除指定角色的聊天历史"""
        try:
            self.db.execute_query(
                "DELETE FROM chat_history WHERE username = ? AND character = ?",
                (username, character)
            )
            return True
        except Exception as e:
            print(f"清除聊天历史出错: {e}")
            return False

    def delete_message(self, username, character, timestamp):
        """删除指定的消息"""
        try:
            self.db.execute_query(
                "DELETE FROM chat_history WHERE username = ? AND character = ? AND timestamp = ?",
                (username, character, timestamp)
            )
            return True
        except Exception as e:
            print(f"删除消息出错: {e}")
            return False

    def search_messages(self, username, query, character=None):
        """搜索聊天消息"""
        try:
            if character:
                messages = self.db.execute_query(
                    "SELECT character, role, content, timestamp FROM chat_history WHERE username = ? AND character = ? AND content LIKE ? ORDER BY timestamp DESC",
                    (username, character, f"%{query}%"), fetch_all=True
                )
            else:
                messages = self.db.execute_query(
                    "SELECT character, role, content, timestamp FROM chat_history WHERE username = ? AND content LIKE ? ORDER BY timestamp DESC",
                    (username, f"%{query}%"), fetch_all=True
                )
            
            return messages
        except Exception as e:
            print(f"搜索消息出错: {e}")
            return []

    def get_user_stats(self, username):
        """获取用户聊天统计信息"""
        try:
            # 总消息数
            total_messages = self.db.execute_query(
                "SELECT COUNT(*) as count FROM chat_history WHERE username = ?",
                (username,), fetch_one=True
            )
            
            # 各角色消息数
            character_stats = self.db.execute_query(
                "SELECT character, COUNT(*) as count FROM chat_history WHERE username = ? GROUP BY character ORDER BY count DESC",
                (username,), fetch_all=True
            )
            
            # 最近活跃时间
            last_activity = self.db.execute_query(
                "SELECT MAX(timestamp) as last_time FROM chat_history WHERE username = ?",
                (username,), fetch_one=True
            )
            
            return {
                'total_messages': total_messages['count'] if total_messages else 0,
                'character_stats': character_stats or [],
                'last_activity': last_activity['last_time'] if last_activity else None
            }
        except Exception as e:
            print(f"获取用户统计出错: {e}")
            return {'total_messages': 0, 'character_stats': [], 'last_activity': None}
