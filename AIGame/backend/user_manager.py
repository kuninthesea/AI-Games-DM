# -*- coding: utf-8 -*-
import hashlib
from datetime import datetime, timedelta
import secrets
from database import DatabaseManager
from database_separation import db_separation_manager
from models.config_manager import config_manager


class UserManager:
    def __init__(self):
        self.db = db_separation_manager

    def register_user(self, username, password):
        """用户注册"""
        try:
            # 检查用户是否已存在
            existing_user = self.db.execute_query(
                "SELECT username FROM users WHERE username = ?",
                (username,), fetch_one=True
            )
            
            if existing_user:
                return False, "用户已存在"
            
            # 创建用户认证信息
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            now = datetime.now().isoformat()
            
            self.db.execute_query(
                "INSERT INTO users (username, password, created_at, last_login) VALUES (?, ?, ?, ?)",
                (username, password_hash, now, now)
            )
            
            # 初始化用户数据
            self.create_user_data(username)
            
            return True, "注册成功"
        except Exception as e:
            print(f"❌ UserManager: 注册失败: {str(e)}")
            return False, f"注册失败: {str(e)}"

    def login_user(self, username, password):
        """用户登录"""
        try:
            # 验证用户认证信息
            user = self.db.execute_query(
                "SELECT username, password FROM users WHERE username = ?",
                (username,), fetch_one=True
            )
            
            if not user:
                return False, "用户不存在"
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if user['password'] != password_hash:
                return False, "密码错误"
            
            # 更新登录时间
            self.db.execute_query(
                "UPDATE users SET last_login = ? WHERE username = ?",
                (datetime.now().isoformat(), username)
            )
            
            # 创建会话令牌
            session_token = self.create_session(username)
            
            return True, {"message": "登录成功", "session_token": session_token}
        except Exception as e:
            return False, f"登录失败: {str(e)}"

    def create_session(self, username):
        """创建用户会话"""
        session_token = secrets.token_urlsafe(32)
        created_at = datetime.now()
        expires_at = created_at + timedelta(hours=24)  # 24小时后过期
        
        self.db.execute_query(
            "INSERT INTO user_sessions (username, session_token, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (username, session_token, created_at.isoformat(), expires_at.isoformat())
        )
        
        return session_token

    def validate_session(self, session_token):
        """验证会话令牌"""
        session = self.db.execute_query(
            "SELECT username, expires_at FROM user_sessions WHERE session_token = ?",
            (session_token,), fetch_one=True
        )
        
        if not session:
            return False, None
        
        expires_at = datetime.fromisoformat(session['expires_at'])
        if datetime.now() > expires_at:
            # 删除过期会话
            self.db.execute_query(
                "DELETE FROM user_sessions WHERE session_token = ?",
                (session_token,)
            )
            return False, None
        
        return True, session['username']

    def create_user_data(self, username):
        """创建用户数据"""
        now = datetime.now().isoformat()
        
        # 插入用户数据
        self.db.execute_query(
            "INSERT INTO user_data (username, hp, mp, max_hp, max_mp, gold, experience, level, attack, defense, critical_rate, critical_damage, created_at, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (username, 100, 50, 100, 50, 100, 0, 1, 10, 5, 5, 150, now, now)
        )
        
        # 初始化装备槽位
        slots = ['weapon', 'armor', 'helmet', 'boots', 'pants', 'shield', 'accessory']
        for slot in slots:
            self.db.execute_query(
                "INSERT INTO user_equipment (username, slot, item_id, equipped_at) VALUES (?, ?, ?, ?)",
                (username, slot, None, None)
            )
        
        # 初始化用户位置 - 默认在家
        self.db.execute_query(
            "INSERT INTO user_locations (username, current_area, current_location, last_updated) VALUES (?, ?, ?, ?)",
            (username, 'novice_village', 'home', now)
        )
        
        return self.get_user_data(username)

    def get_user_data(self, username):
        """获取用户数据"""
        try:
            # 获取基础用户数据
            user_data = self.db.execute_query(
                "SELECT * FROM user_data WHERE username = ?",
                (username,), fetch_one=True
            )
            
            if not user_data:
                return self.create_user_data(username)
            
            # 获取背包数据
            inventory_items = self.db.execute_query(
                "SELECT item_id, quantity FROM user_inventory WHERE username = ?",
                (username,), fetch_all=True
            )
            
            # 获取装备数据
            equipment_items = self.db.execute_query(
                "SELECT slot, item_id, equipped_at FROM user_equipment WHERE username = ?",
                (username,), fetch_all=True
            )
            
            # 组装完整用户数据
            inventory_with_details = []
            for item in inventory_items:
                item_config = config_manager.get_item_by_id(item['item_id'])
                if item_config:
                    inventory_with_details.append({
                        "id": item['item_id'],
                        "name": item_config.get('item_name', item['item_id']),
                        "description": item_config.get('description', ''),
                        "type": item_config.get('item_type', ''),
                        "rarity": item_config.get('rarity', 'common'),
                        "quantity": item['quantity']
                    })
                else:
                    # 如果配置中找不到物品，使用默认值
                    inventory_with_details.append({
                        "id": item['item_id'],
                        "name": item['item_id'],
                        "description": '未知物品',
                        "type": 'unknown',
                        "rarity": 'common',
                        "quantity": item['quantity']
                    })
            
            # 计算装备属性加成
            equipment_stats = {
                'attack': 0,
                'defense': 0,
                'hp': 0,
                'mp': 0,
                'critical_rate': 0,
                'critical_damage': 0
            }
            
            # 遍历装备计算总加成
            for equipment in equipment_items:
                if equipment['item_id']:
                    item_config = config_manager.get_item_by_id(equipment['item_id'])
                    if item_config and 'stats' in item_config:
                        stats = item_config['stats']
                        for stat, value in stats.items():
                            if stat in equipment_stats:
                                equipment_stats[stat] += value

            # 计算总的最大值（基础值 + 装备加成）
            total_max_hp = user_data.get('max_hp', 100) + equipment_stats['hp']
            total_max_mp = user_data.get('max_mp', 50) + equipment_stats['mp']
            
            # 确保当前血量和魔法值不超过最大值
            current_hp = min(user_data['hp'], total_max_hp)
            current_mp = min(user_data['mp'], total_max_mp)

            result = {
                "username": user_data['username'],
                "HP": current_hp,
                "MP": current_mp,
                "max_HP": total_max_hp,
                "max_MP": total_max_mp,
                "base_max_HP": user_data.get('max_hp', 100),
                "base_max_MP": user_data.get('max_mp', 50),
                "gold": user_data['gold'],
                "experience": user_data.get('experience', 0),
                "level": user_data.get('level', 1),
                "attack": user_data.get('attack', 10) + equipment_stats['attack'],
                "defense": user_data.get('defense', 5) + equipment_stats['defense'],
                "critical_rate": user_data.get('critical_rate', 5) + equipment_stats['critical_rate'],
                "critical_damage": user_data.get('critical_damage', 150) + equipment_stats['critical_damage'],
                "base_attack": user_data.get('attack', 10),
                "base_defense": user_data.get('defense', 5),
                "base_critical_rate": user_data.get('critical_rate', 5),
                "base_critical_damage": user_data.get('critical_damage', 150),
                "equipment_stats": equipment_stats,
                "inventory": {
                    "items": inventory_with_details
                },
                "equipment": {},
                "created_at": user_data['created_at'],
                "last_updated": user_data['last_updated']
            }
            
            # 处理装备数据
            for equipment in equipment_items:
                if equipment['item_id']:
                    item_config = config_manager.get_item_by_id(equipment['item_id'])
                    if item_config:
                        result["equipment"][equipment['slot']] = {
                            'id': equipment['item_id'],
                            'name': item_config.get('item_name', equipment['item_id']),
                            'description': item_config.get('description', ''),
                            'type': item_config.get('item_type', ''),
                            'rarity': item_config.get('rarity', 'common'),
                            'equipped_at': equipment['equipped_at']
                        }
                    else:
                        result["equipment"][equipment['slot']] = {
                            'id': equipment['item_id'],
                            'name': equipment['item_id'],
                            'description': '未知装备',
                            'type': 'unknown',
                            'rarity': 'common',
                            'equipped_at': equipment['equipped_at']
                        }
                else:
                    result["equipment"][equipment['slot']] = None
            
            return result
        except Exception as e:
            print(f"获取用户数据出错: {e}")
            return self.create_user_data(username)

    def save_user_data(self, username, data):
        """保存用户数据"""
        try:
            now = datetime.now().isoformat()
            
            # 更新基础用户数据
            self.db.execute_query(
                "UPDATE user_data SET hp = ?, mp = ?, max_hp = ?, max_mp = ?, gold = ?, experience = ?, level = ?, attack = ?, defense = ?, critical_rate = ?, critical_damage = ?, last_updated = ? WHERE username = ?",
                (data['HP'], data['MP'], 
                 data.get('base_max_HP', data.get('max_HP', 100)), 
                 data.get('base_max_MP', data.get('max_MP', 50)),
                 data['gold'], 
                 data.get('experience', 0), data.get('level', 1), 
                 data.get('base_attack', data.get('attack', 10)), 
                 data.get('base_defense', data.get('defense', 5)),
                 data.get('base_critical_rate', data.get('critical_rate', 5)), 
                 data.get('base_critical_damage', data.get('critical_damage', 150)),
                 now, username)
            )
            
            return True
        except Exception as e:
            print(f"保存用户数据出错: {e}")
            return False

    def add_item_to_inventory(self, username, item_id, quantity=1):
        """向背包添加物品"""
        try:
            # 查找是否已有该物品
            existing_item = self.db.execute_query(
                "SELECT id, quantity FROM user_inventory WHERE username = ? AND item_id = ?",
                (username, item_id), fetch_one=True
            )
            
            if existing_item:
                # 更新数量
                new_quantity = existing_item['quantity'] + quantity
                self.db.execute_query(
                    "UPDATE user_inventory SET quantity = ? WHERE id = ?",
                    (new_quantity, existing_item['id'])
                )
            else:
                # 添加新物品
                self.db.execute_query(
                    "INSERT INTO user_inventory (username, item_id, quantity, acquired_at) VALUES (?, ?, ?, ?)",
                    (username, item_id, quantity, datetime.now().isoformat())
                )
            
            return True
        except Exception as e:
            print(f"添加物品到背包出错: {e}")
            return False

    def remove_item_from_inventory(self, username, item_id, quantity=1):
        """从背包移除物品"""
        try:
            existing_item = self.db.execute_query(
                "SELECT id, quantity FROM user_inventory WHERE username = ? AND item_id = ?",
                (username, item_id), fetch_one=True
            )
            
            if existing_item:
                if existing_item['quantity'] <= quantity:
                    # 删除物品
                    self.db.execute_query(
                        "DELETE FROM user_inventory WHERE id = ?",
                        (existing_item['id'],)
                    )
                else:
                    # 减少数量
                    new_quantity = existing_item['quantity'] - quantity
                    self.db.execute_query(
                        "UPDATE user_inventory SET quantity = ? WHERE id = ?",
                        (new_quantity, existing_item['id'])
                    )
            
            return True
        except Exception as e:
            print(f"从背包移除物品出错: {e}")
            return False

    def equip_item(self, username, item_id, slot):
        """装备物品"""
        try:
            # 检查背包中是否有该物品
            inventory_item = self.db.execute_query(
                "SELECT quantity FROM user_inventory WHERE username = ? AND item_id = ?",
                (username, item_id), fetch_one=True
            )
            
            if not inventory_item or inventory_item['quantity'] < 1:
                return False, "背包中没有该物品"
            
            # 获取当前装备
            current_equipment = self.db.execute_query(
                "SELECT item_id FROM user_equipment WHERE username = ? AND slot = ?",
                (username, slot), fetch_one=True
            )
            
            # 如果该槽位已有装备，先卸下
            if current_equipment and current_equipment['item_id']:
                self.add_item_to_inventory(username, current_equipment['item_id'], 1)
            
            # 装备新物品
            self.db.execute_query(
                "UPDATE user_equipment SET item_id = ?, equipped_at = ? WHERE username = ? AND slot = ?",
                (item_id, datetime.now().isoformat(), username, slot)
            )
            
            # 从背包移除
            self.remove_item_from_inventory(username, item_id, 1)
            
            return True, "装备成功"
        except Exception as e:
            return False, f"装备失败: {str(e)}"

    def unequip_item(self, username, slot):
        """卸下装备"""
        try:
            current_equipment = self.db.execute_query(
                "SELECT item_id FROM user_equipment WHERE username = ? AND slot = ?",
                (username, slot), fetch_one=True
            )
            
            if not current_equipment or not current_equipment['item_id']:
                return False, "该槽位没有装备"
            
            item_id = current_equipment['item_id']
            
            # 卸下装备
            self.db.execute_query(
                "UPDATE user_equipment SET item_id = ?, equipped_at = ? WHERE username = ? AND slot = ?",
                (None, None, username, slot)
            )
            
            # 放回背包
            self.add_item_to_inventory(username, item_id, 1)
            
            return True, "卸下成功"
        except Exception as e:
            return False, f"卸下失败: {str(e)}"
