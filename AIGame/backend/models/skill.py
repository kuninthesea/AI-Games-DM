import sqlite3
import os
from typing import List, Dict, Any, Optional
from config import BACKEND_DIR

def get_db():
    """获取数据库连接"""
    db_path = os.path.join(BACKEND_DIR, 'game_data.db')
    return sqlite3.connect(db_path)

class Skill:
    def __init__(self, skill_id=None, name=None, effect=None, damage_multiplier=1.0, mp_cost=0):
        self.skill_id = skill_id
        self.name = name
        self.effect = effect  # 非纯伤害类技能的效果描述
        self.damage_multiplier = damage_multiplier  # 伤害倍率
        self.mp_cost = mp_cost  # MP消耗
    
    def to_dict(self):
        return {
            'skill_id': self.skill_id,
            'name': self.name,
            'effect': self.effect,
            'damage_multiplier': self.damage_multiplier,
            'mp_cost': self.mp_cost
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            skill_id=data.get('skill_id'),
            name=data.get('name'),
            effect=data.get('effect'),
            damage_multiplier=data.get('damage_multiplier', 1.0),
            mp_cost=data.get('mp_cost', 0)
        )

class SkillManager:
    def __init__(self):
        self.init_database()
        self.init_default_skills()
    
    def init_database(self):
        """初始化技能数据库"""
        conn = get_db()
        cursor = conn.cursor()
        
        # 创建技能表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                effect TEXT,
                damage_multiplier REAL DEFAULT 1.0,
                mp_cost INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("技能数据库初始化完成")
    
    def add_skill(self, skill: Skill) -> int:
        """添加新技能"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO skills (name, effect, damage_multiplier, mp_cost)
            VALUES (?, ?, ?, ?)
        ''', (skill.name, skill.effect, skill.damage_multiplier, skill.mp_cost))
        
        skill_id = cursor.lastrowid
        conn.commit()
        print(f"添加技能: {skill.name} (ID: {skill_id})")
        return skill_id
    
    def get_skill(self, skill_id: int) -> Optional[Skill]:
        """获取指定技能"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM skills WHERE skill_id = ?', (skill_id,))
        row = cursor.fetchone()
        
        if row:
            return Skill(
                skill_id=row[0], name=row[1], effect=row[2],
                damage_multiplier=row[3], mp_cost=row[4]
            )
        return None
    
    def get_skill_by_name(self, name: str) -> Optional[Skill]:
        """根据名字获取技能"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM skills WHERE name = ?', (name,))
        row = cursor.fetchone()
        
        if row:
            return Skill(
                skill_id=row[0], name=row[1], effect=row[2],
                damage_multiplier=row[3], mp_cost=row[4]
            )
        return None
    
    def get_all_skills(self) -> List[Skill]:
        """获取所有技能"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM skills ORDER BY skill_id')
        rows = cursor.fetchall()
        
        skills = []
        for row in rows:
            skills.append(Skill(
                skill_id=row[0], name=row[1], effect=row[2],
                damage_multiplier=row[3], mp_cost=row[4]
            ))
        
        return skills
    
    def init_default_skills(self):
        """初始化默认技能"""
        conn = get_db()
        cursor = conn.cursor()
        
        # 检查是否已有技能
        cursor.execute('SELECT COUNT(*) FROM skills')
        if cursor.fetchone()[0] > 0:
            return
        
        # 添加默认技能
        default_skills = [
            Skill(
                name="普通攻击",
                effect=None,  # 纯伤害技能，无额外效果
                damage_multiplier=1.0,  # 1倍攻击力
                mp_cost=0  # 无MP消耗
            ),
            Skill(
                name="重击",
                effect="有几率造成暴击伤害",
                damage_multiplier=1.5,
                mp_cost=5
            ),
            Skill(
                name="防御",
                effect="减少50%受到的伤害",
                damage_multiplier=0.0,  # 无伤害
                mp_cost=0
            ),
            Skill(
                name="治疗",
                effect="恢复自身生命值",
                damage_multiplier=0.0,  # 无伤害
                mp_cost=10
            )
        ]
        
        for skill in default_skills:
            self.add_skill(skill)
        
        print("默认技能初始化完成")

# 全局技能管理器实例
skill_manager = SkillManager()
