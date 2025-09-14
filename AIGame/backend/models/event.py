import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import BACKEND_DIR

def get_db():
    """获取数据库连接"""
    db_path = os.path.join(BACKEND_DIR, 'game_data.db')
    return sqlite3.connect(db_path)

class Event:
    def __init__(self, event_id=None, name=None, event_type=None, condition=None, 
                 result=None, is_active=True, priority=1, cooldown=0, max_triggers=None):
        self.event_id = event_id
        self.name = name
        self.event_type = event_type  # 'battle', 'treasure', 'story', etc.
        self.condition = condition
        self.result = result
        self.is_active = is_active
        self.priority = priority  # 优先级，数字越大优先级越高
        self.cooldown = cooldown  # 冷却时间（秒）
        self.max_triggers = max_triggers  # 最大触发次数，None表示无限制
        
    def to_dict(self):
        return {
            'event_id': self.event_id,
            'name': self.name,
            'event_type': self.event_type,
            'condition': self.condition,
            'result': self.result,
            'is_active': self.is_active,
            'priority': self.priority,
            'cooldown': self.cooldown,
            'max_triggers': self.max_triggers
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            event_id=data.get('event_id'),
            name=data.get('name'),
            event_type=data.get('event_type'),
            condition=data.get('condition'),
            result=data.get('result'),
            is_active=data.get('is_active', True),
            priority=data.get('priority', 1),
            cooldown=data.get('cooldown', 0),
            max_triggers=data.get('max_triggers')
        )

class EventManager:
    def __init__(self):
        self.init_database()
        self.init_default_events()
    
    def init_database(self):
        """初始化事件数据库"""
        conn = get_db()
        cursor = conn.cursor()
        
        # 创建事件表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                condition TEXT NOT NULL,
                result TEXT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                priority INTEGER DEFAULT 1,
                cooldown INTEGER DEFAULT 0,
                max_triggers INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建事件触发记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_triggers (
                trigger_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER,
                user_id INTEGER,
                triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                trigger_count INTEGER DEFAULT 1,
                FOREIGN KEY (event_id) REFERENCES events (event_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        print("事件数据库初始化完成")
    
    def add_event(self, event: Event) -> int:
        """添加新事件"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO events (name, event_type, condition, result, is_active, priority, cooldown, max_triggers)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.name, event.event_type, event.condition, event.result,
            event.is_active, event.priority, event.cooldown, event.max_triggers
        ))
        
        event_id = cursor.lastrowid
        conn.commit()
        print(f"添加事件: {event.name} (ID: {event_id})")
        return event_id
    
    def get_event(self, event_id: int) -> Optional[Event]:
        """获取指定事件"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM events WHERE event_id = ?', (event_id,))
        row = cursor.fetchone()
        
        if row:
            return Event(
                event_id=row[0], name=row[1], event_type=row[2],
                condition=row[3], result=row[4], is_active=row[5],
                priority=row[6], cooldown=row[7], max_triggers=row[8]
            )
        return None
    
    def get_events_by_type(self, event_type: str) -> List[Event]:
        """获取指定类型的所有事件"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM events WHERE event_type = ? AND is_active = TRUE ORDER BY priority DESC', (event_type,))
        rows = cursor.fetchall()
        
        events = []
        for row in rows:
            events.append(Event(
                event_id=row[0], name=row[1], event_type=row[2],
                condition=row[3], result=row[4], is_active=row[5],
                priority=row[6], cooldown=row[7], max_triggers=row[8]
            ))
        
        return events
    
    def get_all_active_events(self) -> List[Event]:
        """获取所有激活的事件"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM events WHERE is_active = TRUE ORDER BY priority DESC, event_type')
        rows = cursor.fetchall()
        
        events = []
        for row in rows:
            events.append(Event(
                event_id=row[0], name=row[1], event_type=row[2],
                condition=row[3], result=row[4], is_active=row[5],
                priority=row[6], cooldown=row[7], max_triggers=row[8]
            ))
        
        return events
    
    def check_event_conditions(self, user_context: Dict[str, Any]) -> List[Event]:
        """检查哪些事件满足触发条件"""
        available_events = []
        all_events = self.get_all_active_events()
        
        user_id = user_context.get('user_id')
        current_location = user_context.get('location', '').lower()
        
        for event in all_events:
            # 检查冷却时间
            if not self._check_cooldown(event.event_id, user_id):
                continue
                
            # 检查最大触发次数
            if not self._check_max_triggers(event.event_id, user_id):
                continue
            
            # 检查条件
            if self._evaluate_condition(event.condition, user_context):
                available_events.append(event)
        
        return available_events
    
    def _evaluate_condition(self, condition: str, user_context: Dict[str, Any]) -> bool:
        """评估事件条件是否满足"""
        condition = condition.lower().strip()
        current_location = user_context.get('location', '').lower()
        
        # 简单的条件匹配逻辑
        if '进入' in condition and '村外森林' in condition:
            return 'village_forest' in current_location
        elif '进入' in condition and '森林' in condition:
            return 'forest' in current_location or 'village_forest' in current_location
        elif '进入' in condition and '村庄' in condition:
            return '村' in current_location or 'village' in current_location
        elif '进入' in condition and '城镇' in condition:
            return '城' in current_location or '镇' in current_location or 'town' in current_location
        
        # 更多条件可以在这里添加
        return False
    
    def _check_cooldown(self, event_id: int, user_id: int) -> bool:
        """检查事件冷却时间"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT triggered_at FROM event_triggers 
            WHERE event_id = ? AND user_id = ? 
            ORDER BY triggered_at DESC LIMIT 1
        ''', (event_id, user_id))
        
        row = cursor.fetchone()
        if not row:
            return True  # 从未触发过
        
        # 获取事件的冷却时间
        event = self.get_event(event_id)
        if not event or event.cooldown == 0:
            return True
        
        # 计算时间差（这里简化处理，实际应该解析时间戳）
        return True  # 简化实现，总是允许触发
    
    def _check_max_triggers(self, event_id: int, user_id: int) -> bool:
        """检查最大触发次数"""
        event = self.get_event(event_id)
        if not event or event.max_triggers is None:
            return True  # 无限制
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM event_triggers 
            WHERE event_id = ? AND user_id = ?
        ''', (event_id, user_id))
        
        trigger_count = cursor.fetchone()[0]
        return trigger_count < event.max_triggers
    
    def trigger_event(self, event_id: int, user_id: int) -> Dict[str, Any]:
        """触发事件"""
        event = self.get_event(event_id)
        if not event:
            return {'success': False, 'message': '事件不存在'}
        
        # 记录触发
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO event_triggers (event_id, user_id)
            VALUES (?, ?)
        ''', (event_id, user_id))
        conn.commit()
        
        # 解析事件结果
        result_data = self._parse_event_result(event)
        
        print(f"触发事件: {event.name}")
        return {
            'success': True,
            'event': event.to_dict(),
            'result': result_data
        }
    
    def _parse_event_result(self, event: Event) -> Dict[str, Any]:
        """解析事件结果"""
        result_data = {
            'type': event.event_type,
            'description': event.result
        }
        
        if event.event_type == 'battle':
            # 解析战斗事件，使用生物系统
            result_text = event.result.lower()
            
            # 导入生物管理器
            from models.creature import creature_manager
            
            # 根据事件描述匹配生物
            enemy_data = None
            if '哥布林' in result_text:
                # 查找哥布林生物
                goblin = creature_manager.get_creature_by_name("普通哥布林")
                if goblin:
                    # 根据事件等级调整难度
                    level_modifier = 1.0
                    if 'lv1' in result_text:
                        level_modifier = 0.8  # 稍微弱一点
                    elif 'lv2' in result_text:
                        level_modifier = 1.2
                    
                    enemy_data = creature_manager.create_battle_instance(
                        goblin.creature_id, level_modifier
                    )
            
            # 如果没有找到对应生物，使用默认数据
            if not enemy_data:
                enemy_data = {
                    'name': '未知敌人',
                    'avatar': '👹',
                    'hp': 30,
                    'maxHp': 30,
                    'attack': 8,
                    'defense': 3,
                    'exp': 10
                }
            
            result_data['enemy'] = enemy_data
        
        return result_data
    
    def init_default_events(self):
        """初始化默认事件"""
        conn = get_db()
        cursor = conn.cursor()
        
        # 检查是否已有事件
        cursor.execute('SELECT COUNT(*) FROM events')
        if cursor.fetchone()[0] > 0:
            return
        
        # 添加默认战斗事件
        default_events = [
            Event(
                name="【战斗】lv1哥布林",
                event_type="battle",
                condition="进入村外森林",
                result="与1个lv1级哥布林战斗",
                priority=5,
                cooldown=300,  # 5分钟冷却
                max_triggers=None  # 无限制
            ),
            Event(
                name="【战斗】野狼",
                event_type="battle", 
                condition="进入深林",
                result="与1只野狼战斗",
                priority=3,
                cooldown=600,
                max_triggers=None
            ),
            Event(
                name="【宝藏】森林宝箱",
                event_type="treasure",
                condition="进入村外森林",
                result="发现了一个神秘的宝箱",
                priority=2,
                cooldown=1800,  # 30分钟
                max_triggers=5  # 最多触发5次
            )
        ]
        
        for event in default_events:
            self.add_event(event)
        
        print("默认事件初始化完成")
    
    def get_event_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """获取用户事件触发历史"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.name, e.event_type, et.triggered_at
            FROM event_triggers et
            JOIN events e ON et.event_id = e.event_id
            WHERE et.user_id = ?
            ORDER BY et.triggered_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        history = []
        for row in rows:
            history.append({
                'name': row[0],
                'type': row[1], 
                'triggered_at': row[2]
            })
        
        return history

# 全局事件管理器实例
event_manager = EventManager()
