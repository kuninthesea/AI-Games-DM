# -*- coding: utf-8 -*-
import sqlite3
import os
import json
from datetime import datetime
from config import BACKEND_DIR

class DatabaseManager:
    def __init__(self):
        self.db_path = os.path.join(BACKEND_DIR, 'game_data.db')
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 用户认证表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT NOT NULL
            )
        ''')
        
        # 用户数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hp INTEGER NOT NULL DEFAULT 100,
                mp INTEGER NOT NULL DEFAULT 50,
                gold INTEGER NOT NULL DEFAULT 100,
                experience INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                attack INTEGER NOT NULL DEFAULT 10,
                defense INTEGER NOT NULL DEFAULT 5,
                critical_rate INTEGER NOT NULL DEFAULT 5,
                critical_damage INTEGER NOT NULL DEFAULT 150,
                created_at TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES users (username)
            )
        ''')
        
        # 用户背包表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                item_id TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                acquired_at TEXT NOT NULL,
                UNIQUE(username, item_id),
                FOREIGN KEY (username) REFERENCES users (username)
            )
        ''')
        
        # 用户装备表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_equipment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                slot TEXT NOT NULL,
                item_id TEXT,
                equipped_at TEXT,
                UNIQUE(username, slot),
                FOREIGN KEY (username) REFERENCES users (username)
            )
        ''')
        
        # 聊天历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                character TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES users (username)
            )
        ''')
        
        # 用户会话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES users (username)
            )
        ''')
        
        # 地图区域表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS map_areas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                area_name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                area_type TEXT NOT NULL DEFAULT 'town',
                created_at TEXT NOT NULL
            )
        ''')
        
        # 地图地点表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS map_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                area_name TEXT NOT NULL,
                location_type TEXT NOT NULL,
                is_accessible INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (area_name) REFERENCES map_areas (area_name)
            )
        ''')
        
        # 用户位置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                current_area TEXT NOT NULL DEFAULT 'novice_village',
                current_location TEXT NOT NULL DEFAULT 'village_center',
                last_updated TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES users (username),
                FOREIGN KEY (current_area) REFERENCES map_areas (area_name),
                FOREIGN KEY (current_location) REFERENCES map_locations (location_name)
            )
        ''')
        
        # 商店表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shop_name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                location_name TEXT NOT NULL,
                description TEXT,
                shop_type TEXT NOT NULL DEFAULT 'general',
                created_at TEXT NOT NULL,
                FOREIGN KEY (location_name) REFERENCES map_locations (location_name)
            )
        ''')
        
        # 商店商品表 (简化版 - 移除is_available列)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shop_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shop_name TEXT NOT NULL,
                item_id TEXT NOT NULL,
                price INTEGER NOT NULL,
                stock INTEGER DEFAULT -1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (shop_name) REFERENCES shops (shop_name)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("数据库初始化完成")
        
        # 初始化地图数据
        self.init_map_data()
        
        # 商店数据现在由JSON配置文件管理，在server_start.py中初始化
        # self.init_shop_data()
        
        # 升级数据库结构
        self.upgrade_database()
    
    def upgrade_database(self):
        """升级数据库结构 - 添加新字段"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查 users 表结构
            cursor.execute("PRAGMA table_info(users)")
            user_columns = [column[1] for column in cursor.fetchall()]
            
            # 如果 users 表缺少 password 字段，说明表结构有问题，需要重建
            if 'password' not in user_columns:
                print("检测到 users 表结构不完整，正在重建...")
                cursor.execute("DROP TABLE IF EXISTS users")
                cursor.execute('''
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        last_login TEXT NOT NULL
                    )
                ''')
                print("重建 users 表完成")
            
            # 检查 user_data 表是否需要添加新字段
            cursor.execute("PRAGMA table_info(user_data)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # 添加经验字段
            if 'experience' not in columns:
                cursor.execute("ALTER TABLE user_data ADD COLUMN experience INTEGER NOT NULL DEFAULT 0")
                print("添加 experience 字段")
            
            # 添加等级字段
            if 'level' not in columns:
                cursor.execute("ALTER TABLE user_data ADD COLUMN level INTEGER NOT NULL DEFAULT 1")
                print("添加 level 字段")
            
            # 添加攻击力字段
            if 'attack' not in columns:
                cursor.execute("ALTER TABLE user_data ADD COLUMN attack INTEGER NOT NULL DEFAULT 10")
                print("添加 attack 字段")
            
            # 添加防御力字段
            if 'defense' not in columns:
                cursor.execute("ALTER TABLE user_data ADD COLUMN defense INTEGER NOT NULL DEFAULT 5")
                print("添加 defense 字段")
            
            # 添加暴击率字段
            if 'critical_rate' not in columns:
                cursor.execute("ALTER TABLE user_data ADD COLUMN critical_rate INTEGER NOT NULL DEFAULT 5")
                print("添加 critical_rate 字段")
            
            # 添加暴击伤害字段  
            if 'critical_damage' not in columns:
                cursor.execute("ALTER TABLE user_data ADD COLUMN critical_damage INTEGER NOT NULL DEFAULT 150")
                print("添加 critical_damage 字段")
            
            # 检查 user_inventory 表的唯一约束
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='user_inventory'")
            table_sql = cursor.fetchone()
            if table_sql and 'UNIQUE(username, item_id)' not in table_sql[0]:
                print("检测到 user_inventory 表缺少唯一约束，正在重建...")
                
                # 备份现有数据
                cursor.execute("SELECT username, item_id, SUM(quantity) as total_quantity, MIN(acquired_at) as first_acquired FROM user_inventory GROUP BY username, item_id")
                inventory_backup = cursor.fetchall()
                
                # 重建表
                cursor.execute("DROP TABLE IF EXISTS user_inventory")
                cursor.execute('''
                    CREATE TABLE user_inventory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        item_id TEXT NOT NULL,
                        quantity INTEGER NOT NULL DEFAULT 1,
                        acquired_at TEXT NOT NULL,
                        UNIQUE(username, item_id),
                        FOREIGN KEY (username) REFERENCES users (username)
                    )
                ''')
                
                # 恢复数据
                for row in inventory_backup:
                    cursor.execute('''
                        INSERT INTO user_inventory (username, item_id, quantity, acquired_at)
                        VALUES (?, ?, ?, ?)
                    ''', (row[0], row[1], row[2], row[3]))
                
                print(f"重建 user_inventory 表完成，恢复了 {len(inventory_backup)} 条记录")
            
            # 确保所有用户都有完整的装备槽位
            cursor.execute("SELECT DISTINCT username FROM users")
            all_users = cursor.fetchall()
            
            required_slots = ['weapon', 'armor', 'helmet', 'boots', 'pants', 'shield', 'accessory']
            
            for user in all_users:
                username = user[0]
                # 检查用户现有的装备槽位
                cursor.execute("SELECT slot FROM user_equipment WHERE username = ?", (username,))
                existing_slots = [row[0] for row in cursor.fetchall()]
                
                # 添加缺失的槽位
                for slot in required_slots:
                    if slot not in existing_slots:
                        cursor.execute(
                            "INSERT INTO user_equipment (username, slot, item_id, equipped_at) VALUES (?, ?, ?, ?)",
                            (username, slot, None, None)
                        )
                        print(f"为用户 {username} 添加装备槽位: {slot}")
            
            conn.commit()
            print("数据库升级完成")
            
        except Exception as e:
            print(f"数据库升级失败: {e}")
        finally:
            conn.close()
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使查询结果可以像字典一样访问
        return conn
    
    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """执行SQL查询"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_one:
                result = cursor.fetchone()
                return dict(result) if result else None
            elif fetch_all:
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def migrate_from_json(self):
        """从JSON文件迁移数据到数据库（可选）"""
        userdata_dir = os.path.join(BACKEND_DIR, '..', 'userdata')
        if not os.path.exists(userdata_dir):
            return
        
        print("开始从JSON文件迁移数据...")
        
        for filename in os.listdir(userdata_dir):
            if filename.endswith('.json') and not filename.endswith('_auth.json') and not filename.endswith('_history.json'):
                username = filename[:-5]  # 移除.json扩展名
                
                try:
                    # 迁移用户数据
                    user_file = os.path.join(userdata_dir, filename)
                    with open(user_file, 'r', encoding='utf-8') as f:
                        user_data = json.load(f)
                    
                    # 迁移认证信息
                    auth_file = os.path.join(userdata_dir, f"{username}_auth.json")
                    if os.path.exists(auth_file):
                        with open(auth_file, 'r', encoding='utf-8') as f:
                            auth_data = json.load(f)
                        
                        # 插入用户认证信息
                        self.execute_query(
                            "INSERT OR REPLACE INTO users (username, password, created_at, last_login) VALUES (?, ?, ?, ?)",
                            (username, auth_data.get('password', ''), 
                             auth_data.get('created_at', datetime.now().isoformat()),
                             auth_data.get('last_login', datetime.now().isoformat()))
                        )
                    
                    # 插入用户数据
                    self.execute_query(
                        "INSERT OR REPLACE INTO user_data (username, hp, mp, gold, experience, level, attack, defense, critical_rate, critical_damage, created_at, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (username, user_data.get('HP', 100), user_data.get('MP', 50), user_data.get('gold', 100),
                         user_data.get('experience', 0), user_data.get('level', 1), 
                         user_data.get('attack', 10), user_data.get('defense', 5),
                         user_data.get('critical_rate', 5), user_data.get('critical_damage', 150),
                         user_data.get('created_at', datetime.now().isoformat()),
                         user_data.get('last_updated', datetime.now().isoformat()))
                    )
                    
                    # 迁移背包数据
                    inventory = user_data.get('inventory', {}).get('items', [])
                    for item in inventory:
                        self.execute_query(
                            "INSERT OR REPLACE INTO user_inventory (username, item_id, quantity, acquired_at) VALUES (?, ?, ?, ?)",
                            (username, item['id'], item.get('quantity', 1), datetime.now().isoformat())
                        )
                    
                    # 迁移装备数据
                    equipment = user_data.get('equipment', {})
                    for slot, item_data in equipment.items():
                        if item_data:
                            self.execute_query(
                                "INSERT OR REPLACE INTO user_equipment (username, slot, item_id, equipped_at) VALUES (?, ?, ?, ?)",
                                (username, slot, item_data.get('id'), item_data.get('equipped_at', datetime.now().isoformat()))
                            )
                    
                    print(f"成功迁移用户 {username} 的数据")
                    
                except Exception as e:
                    print(f"迁移用户 {username} 数据时出错: {e}")
        
        print("数据迁移完成")
    
    def init_map_data(self):
        """初始化地图数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建新手村区域
        cursor.execute('''
            INSERT OR IGNORE INTO map_areas 
            (area_name, display_name, description, area_type, created_at) 
            VALUES (?, ?, ?, ?, ?)
        ''', ('novice_village', '新手村', '一个安全的新手村落，适合初学者探索和学习', 'town', datetime.now().isoformat()))
        
        # 创建外围区域
        cursor.execute('''
            INSERT OR IGNORE INTO map_areas 
            (area_name, display_name, description, area_type, created_at) 
            VALUES (?, ?, ?, ?, ?)
        ''', ('village_outskirts', '村庄外围', '新手村周围的危险区域，有各种怪物出没', 'wilderness', datetime.now().isoformat()))
        
        # 创建新手村的地点
        locations = [
            ('village_center', '村庄中心', '新手村的中心广场，人来人往，是信息交流的好地方', 'novice_village', 'public'),
            ('blacksmith', '铁匠铺', '村里的铁匠铺，可以购买和修理武器装备', 'novice_village', 'shop'),
            ('library', '图书馆', '安静的图书馆，收藏着各种知识和技能书籍', 'novice_village', 'service'),
            ('adventurer_guild', '冒险家公会', '冒险者聚集的地方，可以接取任务和交流经验', 'novice_village', 'guild'),
            ('inn', '旅馆', '温馨的旅馆，提供休息和补给服务', 'novice_village', 'service'),
            ('village_forest', '村外森林', '新手村外的茂密森林，哥布林经常在这里出没，是新手冒险者的试炼之地', 'village_outskirts', 'dungeon')
        ]
        
        for location in locations:
            cursor.execute('''
                INSERT OR IGNORE INTO map_locations 
                (location_name, display_name, description, area_name, location_type, is_accessible, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (*location, 1, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        print("地图数据初始化完成")
    
    def get_user_location(self, username):
        """获取用户当前位置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ul.current_area, ul.current_location, ma.display_name, ml.display_name, ml.description
            FROM user_locations ul
            JOIN map_areas ma ON ul.current_area = ma.area_name
            JOIN map_locations ml ON ul.current_location = ml.location_name
            WHERE ul.username = ?
        ''', (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'current_area': result[0],
                'current_location': result[1],
                'area_display_name': result[2],
                'location_display_name': result[3],
                'location_description': result[4]
            }
        return None
    
    def update_user_location(self, username, new_location):
        """更新用户位置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 检查位置是否存在且可访问
        print(f"🔍 检查位置: {new_location}")
        cursor.execute('''
            SELECT area_name FROM map_locations 
            WHERE location_name = ? AND is_accessible = 1
        ''', (new_location,))
        
        location_data = cursor.fetchone()
        print(f"📍 位置查询结果: {location_data}")
        
        if not location_data:
            # 打印所有可用位置用于调试
            cursor.execute('SELECT location_name, area_name, is_accessible FROM map_locations')
            all_locations = cursor.fetchall()
            print(f"🗺️ 所有可用位置: {all_locations}")
            conn.close()
            return False, "该位置不存在或不可访问"
        
        area_name = location_data[0]
        
        # 更新用户位置
        cursor.execute('''
            INSERT OR REPLACE INTO user_locations 
            (username, current_area, current_location, last_updated) 
            VALUES (?, ?, ?, ?)
        ''', (username, area_name, new_location, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True, "位置更新成功"
    
    def get_area_locations(self, area_name):
        """获取区域内的所有地点"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT location_name, display_name, description, location_type, is_accessible
            FROM map_locations 
            WHERE area_name = ?
            ORDER BY location_type, display_name
        ''', (area_name,))
        
        locations = []
        for row in cursor.fetchall():
            locations.append({
                'location_name': row[0],
                'display_name': row[1],
                'description': row[2],
                'location_type': row[3],
                'is_accessible': bool(row[4])
            })
        
        conn.close()
        return locations
    
    def initialize_user_location(self, username):
        """为新用户初始化位置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO user_locations 
            (username, current_area, current_location, last_updated) 
            VALUES (?, ?, ?, ?)
        ''', (username, 'novice_village', 'village_center', datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    # init_shop_data 方法已删除 - 商店数据现在由JSON配置文件管理
    
    def get_shop_by_location(self, location_name):
        """根据位置获取商店信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT shop_name, display_name, description, shop_type
            FROM shops 
            WHERE location_name = ?
        ''', (location_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'shop_name': result[0],
                'display_name': result[1],
                'description': result[2],
                'shop_type': result[3],
                'location_name': location_name
            }
        return None
    
    def get_shop_items(self, shop_name):
        """获取商店商品列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT si.item_id, si.price, si.stock
            FROM shop_items si
            WHERE si.shop_name = ?
            ORDER BY si.price
        ''', (shop_name,))
        
        items = []
        for row in cursor.fetchall():
            items.append({
                'item_id': row[0],
                'price': row[1],
                'stock': row[2],
                'is_available': True  # 所有商品默认可用
            })
        
        conn.close()
        return items
    
    def purchase_item(self, username, shop_name, item_id, price):
        """购买商品"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查用户金币
            cursor.execute('SELECT gold FROM user_data WHERE username = ?', (username,))
            user_gold_result = cursor.fetchone()
            if not user_gold_result or user_gold_result[0] < price:
                conn.rollback()
                conn.close()
                return False, "金币不足"
            
            # 检查商品库存
            cursor.execute('''
                SELECT stock FROM shop_items 
                WHERE shop_name = ? AND item_id = ?
            ''', (shop_name, item_id))
            
            stock_result = cursor.fetchone()
            if not stock_result:
                conn.rollback()
                conn.close()
                return False, "商品不存在或已下架"
            
            stock = stock_result[0]
            if stock == 0:
                conn.rollback()
                conn.close()
                return False, "商品已售完"
            
            # 扣除金币
            cursor.execute('''
                UPDATE user_data SET gold = gold - ?, last_updated = ?
                WHERE username = ?
            ''', (price, datetime.now().isoformat(), username))
            
            # 减少库存（如果不是无限库存）
            if stock > 0:
                cursor.execute('''
                    UPDATE shop_items SET stock = stock - 1
                    WHERE shop_name = ? AND item_id = ?
                ''', (shop_name, item_id))
            
            # 添加物品到用户背包
            cursor.execute('''
                INSERT INTO user_inventory (username, item_id, quantity, acquired_at)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(username, item_id) DO UPDATE SET
                quantity = quantity + 1,
                acquired_at = ?
            ''', (username, item_id, datetime.now().isoformat(), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            return True, "购买成功"
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"购买失败：{str(e)}"

# 创建数据库管理器实例
db_manager = DatabaseManager()
