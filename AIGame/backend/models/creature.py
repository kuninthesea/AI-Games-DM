import sqlite3
import os
import json
from typing import List, Dict, Any, Optional
from config import BACKEND_DIR
from models.skill import skill_manager

def get_db():
    """获取数据库连接"""
    db_path = os.path.join(BACKEND_DIR, 'game_data.db')
    return sqlite3.connect(db_path)

class Creature:
    def __init__(self, creature_id=None, name=None, description=None, 
                 quality='普通', base_attack=10, base_hp=30, skills=None):
        self.creature_id = creature_id
        self.name = name
        self.description = description
        self.quality = quality  # 普通，稀有，勇者，史诗，传说
        self.base_attack = base_attack
        self.base_hp = base_hp
        self.skills = skills or []  # 技能ID列表
    
    def to_dict(self):
        return {
            'creature_id': self.creature_id,
            'name': self.name,
            'description': self.description,
            'quality': self.quality,
            'base_attack': self.base_attack,
            'base_hp': self.base_hp,
            'skills': self.skills
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            creature_id=data.get('creature_id'),
            name=data.get('name'),
            description=data.get('description'),
            quality=data.get('quality', '普通'),
            base_attack=data.get('base_attack', 10),
            base_hp=data.get('base_hp', 30),
            skills=data.get('skills', [])
        )
    
    def get_skill_objects(self) -> List:
        """获取生物的技能对象列表"""
        skill_objects = []
        for skill_id in self.skills:
            skill = skill_manager.get_skill(skill_id)
            if skill:
                skill_objects.append(skill)
        return skill_objects
    
    def get_quality_multiplier(self) -> float:
        """根据品质获取属性倍率"""
        quality_multipliers = {
            '普通': 1.0,
            '稀有': 1.3,
            '勇者': 1.6,
            '史诗': 2.0,
            '传说': 2.5
        }
        return quality_multipliers.get(self.quality, 1.0)
    
    def get_effective_attack(self) -> int:
        """获取有效攻击力（考虑品质加成）"""
        return int(self.base_attack * self.get_quality_multiplier())
    
    def get_effective_hp(self) -> int:
        """获取有效生命值（考虑品质加成）"""
        return int(self.base_hp * self.get_quality_multiplier())

class CreatureManager:
    def __init__(self):
        self.init_database()
        self.init_default_creatures()
    
    def init_database(self):
        """初始化生物数据库"""
        conn = get_db()
        cursor = conn.cursor()
        
        # 创建生物表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS creatures (
                creature_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                quality TEXT DEFAULT '普通',
                base_attack INTEGER DEFAULT 10,
                base_hp INTEGER DEFAULT 30,
                skills TEXT,  -- JSON格式存储技能ID数组
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("生物数据库初始化完成")
    
    def add_creature(self, creature: Creature) -> int:
        """添加新生物"""
        conn = get_db()
        cursor = conn.cursor()
        
        skills_json = json.dumps(creature.skills)
        
        cursor.execute('''
            INSERT INTO creatures (name, description, quality, base_attack, base_hp, skills)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            creature.name, creature.description, creature.quality,
            creature.base_attack, creature.base_hp, skills_json
        ))
        
        creature_id = cursor.lastrowid
        conn.commit()
        print(f"添加生物: {creature.name} (ID: {creature_id})")
        return creature_id
    
    def get_creature(self, creature_id: int) -> Optional[Creature]:
        """获取指定生物"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM creatures WHERE creature_id = ?', (creature_id,))
        row = cursor.fetchone()
        
        if row:
            skills = json.loads(row[6]) if row[6] else []
            return Creature(
                creature_id=row[0], name=row[1], description=row[2],
                quality=row[3], base_attack=row[4], base_hp=row[5],
                skills=skills
            )
        return None
    
    def get_creature_by_name(self, name: str) -> Optional[Creature]:
        """根据名字获取生物"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM creatures WHERE name = ?', (name,))
        row = cursor.fetchone()
        
        if row:
            skills = json.loads(row[6]) if row[6] else []
            return Creature(
                creature_id=row[0], name=row[1], description=row[2],
                quality=row[3], base_attack=row[4], base_hp=row[5],
                skills=skills
            )
        return None
    
    def get_creatures_by_quality(self, quality: str) -> List[Creature]:
        """根据品质获取生物列表"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM creatures WHERE quality = ? ORDER BY creature_id', (quality,))
        rows = cursor.fetchall()
        
        creatures = []
        for row in rows:
            skills = json.loads(row[6]) if row[6] else []
            creatures.append(Creature(
                creature_id=row[0], name=row[1], description=row[2],
                quality=row[3], base_attack=row[4], base_hp=row[5],
                skills=skills
            ))
        
        return creatures
    
    def get_all_creatures(self) -> List[Creature]:
        """获取所有生物"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM creatures ORDER BY quality, creature_id')
        rows = cursor.fetchall()
        
        creatures = []
        for row in rows:
            skills = json.loads(row[6]) if row[6] else []
            creatures.append(Creature(
                creature_id=row[0], name=row[1], description=row[2],
                quality=row[3], base_attack=row[4], base_hp=row[5],
                skills=skills
            ))
        
        return creatures
    
    def create_battle_instance(self, creature_id: int, level_modifier=1.0) -> Dict[str, Any]:
        """创建战斗实例（用于战斗系统）"""
        creature = self.get_creature(creature_id)
        if not creature:
            return None
        
        # 创建战斗实例数据
        battle_instance = {
            'name': creature.name,
            'avatar': self._get_creature_avatar(creature.name),
            'hp': int(creature.get_effective_hp() * level_modifier),
            'maxHp': int(creature.get_effective_hp() * level_modifier),
            'attack': int(creature.get_effective_attack() * level_modifier),
            'defense': max(1, int(creature.get_effective_attack() * 0.3 * level_modifier)),
            'exp': int(10 * creature.get_quality_multiplier() * level_modifier),
            'skills': creature.get_skill_objects(),
            'quality': creature.quality,
            'description': creature.description
        }
        
        return battle_instance
    
    def _get_creature_avatar(self, name: str) -> str:
        """根据生物名字获取头像"""
        avatar_map = {
            '普通哥布林': '👹',
            '哥布林': '👹',
            '野狼': '🐺',
            '骷髅': '💀',
            '史莱姆': '🟢',
            '巨魔': '👹',
            '龙': '🐉',
            '恶魔': '👿'
        }
        
        for key, avatar in avatar_map.items():
            if key in name:
                return avatar
        
        return '👹'  # 默认头像
    
    def init_default_creatures(self):
        """初始化默认生物"""
        conn = get_db()
        cursor = conn.cursor()
        
        # 检查是否已有生物
        cursor.execute('SELECT COUNT(*) FROM creatures')
        if cursor.fetchone()[0] > 0:
            return
        
        # 获取普通攻击技能ID
        normal_attack = skill_manager.get_skill_by_name("普通攻击")
        normal_attack_id = normal_attack.skill_id if normal_attack else 1
        
        # 添加默认生物
        default_creatures = [
            Creature(
                name="普通哥布林",
                description="最常见的绿皮怪物，虽然弱小但数量众多",
                quality="普通",
                base_attack=8,
                base_hp=25,
                skills=[normal_attack_id]
            ),
            Creature(
                name="精英哥布林",
                description="经过训练的哥布林战士，比普通同类更加强悍",
                quality="稀有",
                base_attack=12,
                base_hp=40,
                skills=[normal_attack_id]
            ),
            Creature(
                name="哥布林首领",
                description="哥布林部族的领导者，拥有强大的战斗技巧",
                quality="勇者",
                base_attack=18,
                base_hp=60,
                skills=[normal_attack_id]
            )
        ]
        
        for creature in default_creatures:
            self.add_creature(creature)
        
        print("默认生物初始化完成")

# 全局生物管理器实例
creature_manager = CreatureManager()
