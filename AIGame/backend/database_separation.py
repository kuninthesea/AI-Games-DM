# -*- coding: utf-8 -*-
"""
数据库分离管理

分为两个数据库：
1. game_data.db - 用户进度、游戏状态等会变化的数据
2. world_data.db - 地图、敌人、物品等配置数据，每次启动时从JSON重新生成
"""
import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, List, Any


class DatabaseSeparationManager:
    def __init__(self, backend_dir: str = None):
        if backend_dir is None:
            # 自动检测backend目录位置
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.backend_dir = current_dir
        else:
            self.backend_dir = backend_dir
        
        self.game_db_path = os.path.join(self.backend_dir, "game_data.db")
        self.world_db_path = os.path.join(self.backend_dir, "world_data.db")
        self.config_dir = os.path.join(self.backend_dir, "control_data")
        
        # 确保backend目录存在
        os.makedirs(self.backend_dir, exist_ok=True)
    
    def init_databases(self):
        """初始化两个数据库"""
        print("📋 初始化分离数据库系统...")
        self.init_game_database()
        self.init_world_database()
        print("✅ 数据库分离系统初始化完成")
    
    def init_game_database(self):
        """初始化游戏数据库（用户进度相关，保持不变）"""
        print("🎮 初始化游戏数据库...")
        
        conn = sqlite3.connect(self.game_db_path)
        cursor = conn.cursor()
        
        # 用户基本信息表
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
                max_hp INTEGER NOT NULL DEFAULT 100,
                max_mp INTEGER NOT NULL DEFAULT 50,
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
        
        # 用户位置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                current_area TEXT NOT NULL DEFAULT 'novice_village',
                current_location TEXT NOT NULL DEFAULT 'home',
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
                FOREIGN KEY (username) REFERENCES users (username)
            )
        ''')
        
        # 聊天记录表
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
        
        # 房间系统相关表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                room_id TEXT PRIMARY KEY,
                host TEXT NOT NULL,
                max_users INTEGER NOT NULL DEFAULT 4,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS room_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                username TEXT NOT NULL,
                joined_at TEXT NOT NULL,
                FOREIGN KEY (room_id) REFERENCES rooms (room_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS room_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id TEXT NOT NULL,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                message_type TEXT NOT NULL DEFAULT 'chat',
                target_user TEXT,
                timestamp INTEGER NOT NULL,
                FOREIGN KEY (room_id) REFERENCES rooms (room_id)
            )
        ''')
        
        # 为现有数据库添加新字段（向后兼容）
        try:
            cursor.execute('ALTER TABLE user_data ADD COLUMN max_hp INTEGER NOT NULL DEFAULT 100')
            print("✅ 已添加max_hp字段")
        except sqlite3.OperationalError:
            pass  # 字段已存在
        
        try:
            cursor.execute('ALTER TABLE user_data ADD COLUMN max_mp INTEGER NOT NULL DEFAULT 50')
            print("✅ 已添加max_mp字段")
        except sqlite3.OperationalError:
            pass  # 字段已存在
        
        # 更新现有用户的最大值（如果当前值大于默认最大值）
        cursor.execute('''
            UPDATE user_data 
            SET max_hp = CASE 
                WHEN hp > max_hp THEN hp 
                ELSE max_hp 
            END,
            max_mp = CASE 
                WHEN mp > max_mp THEN mp 
                ELSE max_mp 
            END
        ''')
        
        conn.commit()
        conn.close()
        print("✅ 游戏数据库初始化完成")
    
    def init_world_database(self):
        """初始化世界数据库（从JSON配置重新生成）"""
        print("🌍 初始化世界数据库...")
        
        # 删除现有的世界数据库（每次重新生成）
        if os.path.exists(self.world_db_path):
            os.remove(self.world_db_path)
            print("🗑️ 已删除旧的世界数据库")
        
        conn = sqlite3.connect(self.world_db_path)
        cursor = conn.cursor()
        
        # 区域表
        cursor.execute('''
            CREATE TABLE map_areas (
                area_id INTEGER PRIMARY KEY AUTOINCREMENT,
                area_name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                area_type TEXT NOT NULL,
                is_accessible BOOLEAN DEFAULT 1,
                created_at TEXT NOT NULL
            )
        ''')
        
        # 地点表
        cursor.execute('''
            CREATE TABLE map_locations (
                location_id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                area_name TEXT NOT NULL,
                location_type TEXT NOT NULL,
                is_accessible BOOLEAN DEFAULT 1,
                interactions TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # 生物表
        cursor.execute('''
            CREATE TABLE creatures (
                creature_id TEXT PRIMARY KEY,
                creature_name TEXT NOT NULL,
                creature_type TEXT NOT NULL,
                rarity TEXT NOT NULL,
                level INTEGER NOT NULL,
                avatar TEXT,
                description TEXT,
                base_stats TEXT NOT NULL,
                skills TEXT,
                ai_behavior TEXT,
                experience_reward INTEGER,
                gold_reward TEXT,
                item_drops TEXT,
                habitat TEXT,
                spawn_conditions TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # 物品表
        cursor.execute('''
            CREATE TABLE items (
                item_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                item_type TEXT NOT NULL,
                sub_type TEXT,
                rarity TEXT NOT NULL,
                base_price INTEGER NOT NULL,
                stats TEXT,
                requirements TEXT,
                effects TEXT,
                consumable BOOLEAN DEFAULT 0,
                stackable BOOLEAN DEFAULT 1,
                max_stack INTEGER DEFAULT 99,
                created_at TEXT NOT NULL
            )
        ''')
        
        # 商店表
        cursor.execute('''
            CREATE TABLE shops (
                shop_id TEXT PRIMARY KEY,
                shop_name TEXT NOT NULL,
                description TEXT,
                shop_type TEXT NOT NULL,
                location TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # 商店物品表
        cursor.execute('''
            CREATE TABLE shop_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shop_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                price INTEGER NOT NULL,
                stock INTEGER DEFAULT -1,
                created_at TEXT NOT NULL,
                FOREIGN KEY (shop_id) REFERENCES shops (shop_id),
                FOREIGN KEY (item_id) REFERENCES items (item_id)
            )
        ''')
        
        # 从JSON配置文件加载数据
        self._load_world_data_from_json(cursor)
        
        conn.commit()
        conn.close()
        print("✅ 世界数据库初始化完成")
    
    def _load_world_data_from_json(self, cursor):
        """从JSON配置文件加载世界数据"""
        now = datetime.now().isoformat()
        
        # 加载地图数据
        self._load_location_data(cursor, now)
        
        # 加载生物数据
        self._load_creature_data(cursor, now)
        
        # 加载物品数据（如果存在）
        self._load_item_data(cursor, now)
        
        # 加载商店数据（如果存在）
        self._load_shop_data(cursor, now)
    
    def _load_location_data(self, cursor, now):
        """加载位置数据"""
        print("📍 加载位置数据...")
        
        location_config_path = os.path.join(self.config_dir, 'location_control.json')
        
        if os.path.exists(location_config_path):
            with open(location_config_path, 'r', encoding='utf-8') as f:
                location_data = json.load(f)
            
            # 首先插入区域数据（从areas数组）
            for area in location_data.get('areas', []):
                cursor.execute('''
                    INSERT OR IGNORE INTO map_areas (area_name, display_name, description, area_type, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    area.get('area_id'),
                    area.get('display_name', area.get('area_name', '未知区域')),
                    area.get('description', f"区域：{area.get('display_name', '未知区域')}"),
                    area.get('area_type', 'unknown'),
                    now
                ))
                print(f"  📍 区域: {area.get('display_name')} ({area.get('area_id')})")
            
            # 插入位置数据
            for location in location_data.get('locations', []):
                interactions_json = json.dumps(location.get('interactions', []), ensure_ascii=False)
                
                # 确保所有必需字段都有值，优先使用location_id作为主键
                location_name = location.get('location_id') or location.get('location_name')
                display_name = location.get('display_name') or location.get('location_name') or location.get('location_id')
                description = location.get('description', f"位置：{display_name}")
                area_name = location.get('area_id') or location.get('area', 'novice_village')
                location_type = location.get('type') or location.get('location_type', 'unknown')
                
                cursor.execute('''
                    INSERT OR REPLACE INTO map_locations (
                        location_name, display_name, description, area_name, 
                        location_type, is_accessible, interactions, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    location_name,
                    display_name,
                    description,
                    area_name,
                    location_type,
                    location.get('is_accessible', True),
                    interactions_json,
                    now
                ))
                print(f"    📍 位置: {display_name} ({location_name})")
        else:
            print("⚠️ 位置配置文件不存在，使用默认配置")
            self._load_default_locations(cursor, now)
    
    def _load_default_locations(self, cursor, now):
        """加载默认位置配置"""
        # 默认区域
        default_areas = [
            ('novice_village', '新手村', '一个安全的新手村落', 'town'),
            ('village_outskirts', '村庄外围', '新手村周围的危险区域', 'wilderness')
        ]
        
        for area in default_areas:
            cursor.execute('''
                INSERT INTO map_areas (area_name, display_name, description, area_type, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (*area, now))
        
        # 默认位置
        default_locations = [
            ('home', '家', '你的温馨小屋', 'novice_village', 'safe_zone', True, '[]'),
            ('market', '市场', '热闹的村庄市场', 'novice_village', 'commercial', True, '[]'),
            ('blacksmith', '铁匠铺', '火花四溅的铁匠铺', 'novice_village', 'shop', True, '[]'),
            ('library', '图书馆', '安静的图书馆', 'novice_village', 'shop', True, '[]'),
            ('forest', '村外森林', '郁郁葱葱的森林', 'village_outskirts', 'wilderness', True, '[]')
        ]
        
        for location in default_locations:
            cursor.execute('''
                INSERT INTO map_locations (
                    location_name, display_name, description, area_name, 
                    location_type, is_accessible, interactions, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*location, now))
    
    def _load_creature_data(self, cursor, now):
        """加载生物数据"""
        print("👹 加载生物数据...")
        
        creature_config_path = os.path.join(self.config_dir, 'creature_control.json')
        
        if os.path.exists(creature_config_path):
            with open(creature_config_path, 'r', encoding='utf-8') as f:
                creature_data = json.load(f)
            
            for creature in creature_data.get('creatures', []):
                cursor.execute('''
                    INSERT OR REPLACE INTO creatures (
                        creature_id, creature_name, creature_type, rarity, level, avatar,
                        description, base_stats, skills, ai_behavior, experience_reward,
                        gold_reward, item_drops, habitat, spawn_conditions, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    creature.get('creature_id'),
                    creature.get('creature_name'),
                    creature.get('creature_type'),
                    creature.get('rarity'),
                    creature.get('level'),
                    creature.get('avatar', '👹'),
                    creature.get('description'),
                    json.dumps(creature.get('base_stats', {}), ensure_ascii=False),
                    json.dumps(creature.get('skills', []), ensure_ascii=False),
                    creature.get('ai_behavior'),
                    creature.get('experience_reward'),
                    json.dumps(creature.get('gold_reward', {}), ensure_ascii=False),
                    json.dumps(creature.get('item_drops', []), ensure_ascii=False),
                    json.dumps(creature.get('habitat', []), ensure_ascii=False),
                    json.dumps(creature.get('spawn_conditions', {}), ensure_ascii=False),
                    now
                ))
                print(f"  👹 生物: {creature.get('creature_name')} ({creature.get('creature_id')})")
        else:
            print("⚠️ 生物配置文件不存在")
    
    def _load_item_data(self, cursor, now):
        """加载物品数据"""
        print("📦 加载物品数据...")
        
        item_config_path = os.path.join(self.config_dir, 'item_control.json')
        
        if os.path.exists(item_config_path):
            with open(item_config_path, 'r', encoding='utf-8') as f:
                item_data = json.load(f)
            
            for item in item_data.get('items', []):
                # 确保必要字段存在
                item_name = item.get('item_name') or item.get('name') or f"物品_{item.get('item_id', 'unknown')}"
                
                cursor.execute('''
                    INSERT OR REPLACE INTO items (
                        item_id, name, description, item_type, sub_type, rarity,
                        base_price, stats, requirements, effects, consumable,
                        stackable, max_stack, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.get('item_id'),
                    item_name,
                    item.get('description', ''),
                    item.get('item_type'),
                    item.get('sub_type', ''),
                    item.get('rarity', 'common'),
                    item.get('base_price', 0),
                    json.dumps(item.get('stats', {}), ensure_ascii=False),
                    json.dumps(item.get('requirements', {}), ensure_ascii=False),
                    json.dumps(item.get('effects', []), ensure_ascii=False),
                    item.get('consumable', False),
                    item.get('stackable', True),
                    item.get('max_stack', 99),
                    now
                ))
                print(f"  📦 物品: {item_name} ({item.get('item_id')})")
        else:
            print("⚠️ 物品配置文件不存在")
    
    def _load_shop_data(self, cursor, now):
        """加载商店数据"""
        print("🏪 加载商店数据...")
        
        shop_config_path = os.path.join(self.config_dir, 'shop_control.json')
        
        if os.path.exists(shop_config_path):
            with open(shop_config_path, 'r', encoding='utf-8') as f:
                shop_data = json.load(f)
            
            for shop in shop_data.get('shops', []):
                # 使用shop_name作为shop_id（如果没有单独的shop_id）
                shop_id = shop.get('shop_id') or shop.get('shop_name')
                location = shop.get('location') or shop.get('location_name')
                
                cursor.execute('''
                    INSERT OR REPLACE INTO shops (
                        shop_id, shop_name, description, shop_type, location, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    shop_id,
                    shop.get('shop_name'),
                    shop.get('description', ''),
                    shop.get('shop_type', 'general'),
                    location,
                    now
                ))
                
                # 插入商店物品
                for item in shop.get('items', []):
                    cursor.execute('''
                        INSERT OR REPLACE INTO shop_items (
                            shop_id, item_id, price, stock, created_at
                        ) VALUES (?, ?, ?, ?, ?)
                    ''', (
                        shop_id,  # 使用前面计算的shop_id变量
                        item.get('item_id'),
                        item.get('price', 0),
                        item.get('stock', -1),
                        now
                    ))
                
                print(f"  🏪 商店: {shop.get('shop_name')} ({shop_id})")
        else:
            print("⚠️ 商店配置文件不存在")

    def get_user_location(self, username):
        """获取用户当前位置"""
        try:
            # 从用户数据库获取用户位置
            conn = sqlite3.connect(self.game_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT current_area, current_location, last_updated
                FROM user_locations 
                WHERE username = ?
            ''', (username,))
            
            user_location = cursor.fetchone()
            conn.close()
            
            if not user_location:
                return None
                
            current_area, current_location, last_updated = user_location
            
            # 从世界数据库获取位置详细信息
            world_conn = sqlite3.connect(self.world_db_path)
            world_cursor = world_conn.cursor()
            
            world_cursor.execute('''
                SELECT display_name, description, area_name, location_type, is_accessible
                FROM map_locations 
                WHERE location_name = ?
            ''', (current_location,))
            
            location_info = world_cursor.fetchone()
            world_conn.close()
            
            if location_info:
                return {
                    'current_area': current_area,
                    'current_location': current_location,
                    'area_display_name': current_area,
                    'location_display_name': location_info[0],
                    'description': location_info[1],
                    'area_name': location_info[2],         # 修正：area_name
                    'location_type': location_info[3],     # 修正：location_type  
                    'is_accessible': location_info[4],     # 修正：is_accessible
                    'last_updated': last_updated
                }
            else:
                # 如果世界数据库中没有找到位置信息，返回基本信息
                return {
                    'current_area': current_area,
                    'current_location': current_location,
                    'area_display_name': current_area,
                    'location_display_name': current_location,
                    'description': '位置描述将显示在这里..',
                    'last_updated': last_updated
                }
                
        except Exception as e:
            print(f"❌ 获取用户位置失败: {e}")
            return None

    def initialize_user_location(self, username):
        """为新用户初始化位置"""
        try:
            conn = sqlite3.connect(self.game_db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_locations 
                (username, current_area, current_location, last_updated) 
                VALUES (?, ?, ?, ?)
            ''', (username, 'novice_village', 'home', now))
            
            conn.commit()
            conn.close()
            
            print(f"✅ 用户 {username} 位置初始化完成")
            return True
            
        except Exception as e:
            print(f"❌ 初始化用户位置失败: {e}")
            return False

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """执行SQL查询的通用方法，兼容旧的DatabaseManager接口"""
        try:
            # 判断查询类型，决定使用哪个数据库
            query_lower = query.lower().strip()
            
            # 用户相关的表使用游戏数据库 (包括user_sessions, chat_history等)
            if any(table in query_lower for table in ['users', 'user_data', 'user_locations', 'user_inventory', 'user_equipment', 'user_sessions', 'chat_history', 'rooms', 'room_users', 'room_messages']):
                db_path = self.game_db_path
            else:
                # 其他表使用世界数据库 (creatures, items, shops, map_locations等)
                db_path = self.world_db_path
            
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            result = None
            if fetch_one:
                row = cursor.fetchone()
                result = dict(row) if row else None
            elif fetch_all:
                rows = cursor.fetchall()
                result = [dict(row) for row in rows] if rows else []
            
            # 如果是INSERT, UPDATE, DELETE等修改操作，需要提交
            if query_lower.startswith(('insert', 'update', 'delete')):
                conn.commit()
            
            conn.close()
            return result
            
        except Exception as e:
            print(f"❌ 数据库查询失败: {e}")
            raise e

    def get_area_locations(self, area_name):
        """获取区域内的所有地点"""
        try:
            conn = sqlite3.connect(self.world_db_path)
            conn.row_factory = sqlite3.Row
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
                    'location_name': row['location_name'],
                    'display_name': row['display_name'],
                    'description': row['description'],
                    'location_type': row['location_type'],
                    'is_accessible': bool(row['is_accessible'])
                })
            
            conn.close()
            return locations
            
        except Exception as e:
            print(f"❌ 获取区域地点失败: {e}")
            return []

    def get_shop_by_location(self, location_name):
        """根据位置获取商店信息"""
        try:
            conn = sqlite3.connect(self.world_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT shop_name, shop_name as display_name, description, shop_type
                FROM shops 
                WHERE location = ?
            ''', (location_name,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'shop_name': result['shop_name'],
                    'display_name': result['display_name'],
                    'description': result['description'],
                    'shop_type': result['shop_type'],
                    'location_name': location_name
                }
            return None
        except Exception as e:
            print(f"❌ 获取商店信息失败: {e}")
            return None
    
    def get_shop_items(self, shop_name):
        """获取商店商品列表"""
        try:
            conn = sqlite3.connect(self.world_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT si.item_id, si.price, si.stock
                FROM shop_items si
                JOIN shops s ON si.shop_id = s.shop_id
                WHERE s.shop_name = ?
                ORDER BY si.price
            ''', (shop_name,))
            
            items = []
            for row in cursor.fetchall():
                items.append({
                    'item_id': row['item_id'],
                    'price': row['price'],
                    'stock': row['stock'],
                    'is_available': True  # 所有商品默认可用
                })
            
            conn.close()
            return items
        except Exception as e:
            print(f"❌ 获取商店商品失败: {e}")
            return []
    
    def purchase_item(self, username, shop_name, item_id, price):
        """购买商品"""
        # 用户数据使用游戏数据库
        game_conn = sqlite3.connect(self.game_db_path)
        # 商店数据使用世界数据库
        world_conn = sqlite3.connect(self.world_db_path)
        
        try:
            game_cursor = game_conn.cursor()
            world_cursor = world_conn.cursor()
            
            # 检查用户金币
            game_cursor.execute('SELECT gold FROM user_data WHERE username = ?', (username,))
            user_gold_result = game_cursor.fetchone()
            if not user_gold_result or user_gold_result[0] < price:
                game_conn.close()
                world_conn.close()
                return False, "金币不足"
            
            # 检查商品库存
            world_cursor.execute('''
                SELECT si.stock FROM shop_items si
                JOIN shops s ON si.shop_id = s.shop_id
                WHERE s.shop_name = ? AND si.item_id = ?
            ''', (shop_name, item_id))
            
            stock_result = world_cursor.fetchone()
            if not stock_result:
                game_conn.close()
                world_conn.close()
                return False, "商品不存在或已下架"
            
            stock = stock_result[0]
            if stock == 0:
                game_conn.close()
                world_conn.close()
                return False, "商品已售完"
            
            # 扣除金币
            game_cursor.execute('''
                UPDATE user_data SET gold = gold - ?, last_updated = ?
                WHERE username = ?
            ''', (price, datetime.now().isoformat(), username))
            
            # 减少库存（如果不是无限库存）
            if stock > 0:
                world_cursor.execute('''
                    UPDATE shop_items SET stock = stock - 1
                    WHERE shop_id IN (SELECT shop_id FROM shops WHERE shop_name = ?) AND item_id = ?
                ''', (shop_name, item_id))
            
            # 添加物品到用户背包
            game_cursor.execute('''
                INSERT INTO user_inventory (username, item_id, quantity, acquired_at)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(username, item_id) DO UPDATE SET
                quantity = quantity + 1,
                acquired_at = ?
            ''', (username, item_id, datetime.now().isoformat(), datetime.now().isoformat()))
            
            game_conn.commit()
            world_conn.commit()
            game_conn.close()
            world_conn.close()
            return True, "购买成功"
            
        except Exception as e:
            game_conn.rollback()
            world_conn.rollback()
            game_conn.close()
            world_conn.close()
            return False, f"购买失败：{str(e)}"

    def update_user_location(self, username, new_location):
        """更新用户位置"""
        # 位置信息在世界数据库，用户位置在游戏数据库
        world_conn = sqlite3.connect(self.world_db_path)
        game_conn = sqlite3.connect(self.game_db_path)
        
        try:
            world_cursor = world_conn.cursor()
            game_cursor = game_conn.cursor()
            
            # 检查位置是否存在且可访问
            print(f"🔍 检查位置: {new_location}")
            world_cursor.execute('''
                SELECT area_name FROM map_locations 
                WHERE location_name = ? AND is_accessible = 1
            ''', (new_location,))
            
            location_data = world_cursor.fetchone()
            print(f"📍 位置查询结果: {location_data}")
            
            if not location_data:
                # 打印所有可用位置用于调试
                world_cursor.execute('SELECT location_name, area_name, is_accessible FROM map_locations')
                all_locations = world_cursor.fetchall()
                print(f"🗺️ 所有可用位置: {all_locations}")
                world_conn.close()
                game_conn.close()
                return False, "该位置不存在或不可访问"
            
            area_name = location_data[0]
            
            # 更新用户位置
            game_cursor.execute('''
                INSERT OR REPLACE INTO user_locations 
                (username, current_area, current_location, last_updated) 
                VALUES (?, ?, ?, ?)
            ''', (username, area_name, new_location, datetime.now().isoformat()))
            
            game_conn.commit()
            world_conn.close()
            game_conn.close()
            return True, "位置更新成功"
            
        except Exception as e:
            world_conn.close()
            game_conn.close()
            return False, f"位置更新失败：{str(e)}"


# 全局数据库分离管理器实例
db_separation_manager = DatabaseSeparationManager()
