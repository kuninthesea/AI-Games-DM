# JSON配置文件编辑指南

## 概述
本TRPG游戏系统支持通过修改JSON配置文件来管理游戏内容，包括怪物、地图、物品、商店等。配置文件位于 `backend/control_data/` 目录中。

**重要提示：** 修改JSON文件后，需要重启服务器才能生效。系统会自动从JSON文件重新加载配置到数据库中。

---

## 配置文件说明

### 1. 怪物配置 (`creature_control.json`)

#### 基本结构
```json
{
  "creatures": [
    {
      "creature_id": "goblin_common_1",
      "creature_name": "普通哥布林", 
      "creature_type": "goblin",
      "rarity": "common",
      "level": 1,
      "avatar": "👹",
      "description": "森林中常见的绿皮小怪物",
      "base_stats": {
        "hp": 30,
        "mp": 10,
        "attack": 8,
        "defense": 3,
        "agility": 12,
        "intelligence": 5
      },
      "skills": ["basic_attack", "goblin_scratch"],
      "ai_behavior": "aggressive",
      "experience_reward": 15,
      "gold_reward": {
        "min": 3,
        "max": 8
      },
      "item_drops": [
        {
          "item_id": "potion_health_small",
          "drop_rate": 0.3
        }
      ],
      "habitat": ["forest"],
      "spawn_conditions": {
        "location": "forest",
        "player_level_min": 1,
        "player_level_max": 5
      }
    }
  ]
}
```

#### 字段说明
- `creature_id`: 唯一标识符，建议使用 `类型_稀有度_等级` 格式
- `creature_name`: 显示名称
- `creature_type`: 怪物类型（如 goblin, dragon, undead）
- `rarity`: 稀有度（common, uncommon, rare, epic, legendary）
- `level`: 等级
- `avatar`: 显示图标（支持emoji）
- `description`: 描述文本
- `base_stats`: 基础属性
  - `hp`: 生命值
  - `mp`: 魔法值
  - `attack`: 攻击力
  - `defense`: 防御力
  - `agility`: 敏捷
  - `intelligence`: 智力
- `skills`: 技能列表（字符串数组）
- `ai_behavior`: AI行为模式（aggressive, defensive, neutral, coward）
- `experience_reward`: 击败后获得的经验值
- `gold_reward`: 金币奖励范围
- `item_drops`: 掉落物品列表
- `habitat`: 栖息地列表
- `spawn_conditions`: 出现条件

---

### 2. 地图配置 (`location_control.json`)

#### 基本结构
```json
{
  "areas": [
    {
      "area_id": "novice_village",
      "area_name": "新手村",
      "display_name": "新手村",
      "description": "一个安全的新手村落",
      "area_type": "town",
      "safety_level": "safe"
    }
  ],
  "locations": [
    {
      "location_id": "home",
      "location_name": "家",
      "display_name": "家",
      "description": "你的温馨小屋",
      "area_id": "novice_village",
      "type": "safe_zone",
      "connections": ["market", "blacksmith"],
      "interactions": [
        {
          "interaction_name": "与木偶假人战斗",
          "interaction_type": "fight",
          "event_id": "training_dummy_battle",
          "conditions": {}
        }
      ],
      "coordinates": {"x": 100, "y": 100}
    }
  ]
}
```

#### 字段说明

**区域配置 (areas)**
- `area_id`: 区域唯一标识符
- `area_name`: 区域名称
- `display_name`: 显示名称
- `description`: 区域描述
- `area_type`: 区域类型（town, wilderness, dungeon）
- `safety_level`: 安全等级（safe, dangerous, hostile）

**位置配置 (locations)**
- `location_id`: 位置唯一标识符
- `location_name`: 位置名称
- `display_name`: 显示名称
- `description`: 位置描述
- `area_id`: 所属区域ID
- `type`: 位置类型（safe_zone, shop, commercial, wilderness）
- `connections`: 连接的其他位置列表
- `interactions`: 可用互动选项
- `coordinates`: 坐标（可选）

**互动选项配置**
- `interaction_name`: 互动名称
- `interaction_type`: 互动类型（fight, healing, shop, repair）
- `event_id`: 关联的事件ID
- `conditions`: 触发条件（可选）

---

### 3. 物品配置 (`item_control.json`)

#### 基本结构
```json
{
  "items": [
    {
      "item_id": "sword_iron",
      "item_name": "铁剑",
      "item_type": "weapon",
      "rarity": "common",
      "description": "标准的铁制长剑",
      "stats": {
        "attack": 15,
        "critical_rate": 5
      },
      "level_requirement": 1,
      "base_price": 100,
      "stackable": false,
      "max_stack": 1
    }
  ]
}
```

#### 字段说明
- `item_id`: 物品唯一标识符
- `item_name`: 物品名称
- `item_type`: 物品类型
  - 武器：`weapon`
  - 防具：`helmet`, `armor`, `boots`
  - 消耗品：`potion`
  - 任务物品：`quest`
  - 材料：`material`
- `rarity`: 稀有度（common, uncommon, rare, epic, legendary）
- `description`: 物品描述
- `stats`: 属性加成
  - `attack`: 攻击力
  - `defense`: 防御力
  - `hp`: 生命值
  - `mp`: 魔法值
  - `critical_rate`: 暴击率
  - `agility`: 敏捷
- `level_requirement`: 等级需求
- `base_price`: 基础价格
- `stackable`: 是否可堆叠
- `max_stack`: 最大堆叠数量
- `consumable`: 是否为消耗品
- `effects`: 使用效果（对于消耗品）

---

### 4. 商店配置 (`shop_control.json`)

#### 基本结构
```json
{
  "shops": [
    {
      "shop_id": "blacksmith_shop",
      "shop_name": "铁匠铺",
      "description": "出售武器和防具的铁匠铺",
      "shop_type": "equipment",
      "location": "blacksmith",
      "items": [
        {
          "item_id": "sword_iron",
          "price": 100,
          "stock": -1,
          "availability": "always"
        }
      ]
    }
  ]
}
```

#### 字段说明
- `shop_id`: 商店唯一标识符
- `shop_name`: 商店名称
- `description`: 商店描述
- `shop_type`: 商店类型（equipment, potion, general, special）
- `location`: 商店所在位置
- `items`: 商店物品列表
  - `item_id`: 物品ID
  - `price`: 售价（-1表示使用物品基础价格）
  - `stock`: 库存（-1表示无限库存）
  - `availability`: 可用性（always, random, quest_dependent）

---

### 5. 事件配置 (`event_control.json`)

#### 基本结构
```json
{
  "events": [
    {
      "event_id": "forest_goblin_encounter",
      "event_name": "森林哥布林遭遇",
      "event_type": "battle",
      "description": "在森林中遭遇了野生哥布林",
      "trigger_conditions": {
        "location": "forest",
        "trigger_type": "location_enter",
        "chance": 0.8,
        "player_level_min": 1,
        "player_level_max": 10
      },
      "event_data": {
        "battle_type": "creature_encounter",
        "creatures": [
          {
            "creature_id": "goblin_common_1",
            "spawn_chance": 0.7
          }
        ],
        "flee_allowed": true,
        "auto_start": true
      },
      "repeatable": true,
      "cooldown": 0
    }
  ]
}
```

#### 字段说明
- `event_id`: 事件唯一标识符
- `event_name`: 事件名称
- `event_type`: 事件类型（battle, shop, healing, story）
- `description`: 事件描述
- `trigger_conditions`: 触发条件
  - `location`: 触发位置
  - `trigger_type`: 触发类型（location_enter, interaction, random）
  - `chance`: 触发概率（0-1）
  - `player_level_min/max`: 玩家等级范围
- `event_data`: 事件数据（根据事件类型不同而不同）
- `repeatable`: 是否可重复
- `cooldown`: 冷却时间（秒）

---

### 6. 技能配置 (`skill_control.json`)

#### 基本结构
```json
{
  "skills": [
    {
      "skill_id": "basic_attack",
      "skill_name": "基础攻击",
      "description": "最基本的攻击方式",
      "skill_type": "attack",
      "mp_cost": 0,
      "damage_multiplier": 1.0,
      "effects": [],
      "cooldown": 0
    }
  ]
}
```

---

## 修改指南

### 添加新怪物
1. 打开 `creature_control.json`
2. 在 `creatures` 数组中添加新的怪物配置
3. 确保 `creature_id` 唯一
4. 重启服务器

### 添加新地图区域
1. 打开 `location_control.json`
2. 在 `areas` 数组中添加新区域
3. 在 `locations` 数组中添加该区域的位置
4. 重启服务器

### 添加新物品
1. 打开 `item_control.json`
2. 在 `items` 数组中添加新物品配置
3. 确保 `item_id` 唯一
4. 重启服务器

### 修改商店库存
1. 打开 `shop_control.json`
2. 找到对应商店配置
3. 修改 `items` 数组中的物品列表
4. 重启服务器

---

## 注意事项

1. **JSON格式**: 确保JSON格式正确，注意逗号和引号
2. **唯一ID**: 所有ID必须在其类型中唯一
3. **依赖关系**: 确保引用的ID存在（如物品ID、位置ID等）
4. **重启服务器**: 修改后必须重启服务器才能生效
5. **备份**: 修改前建议备份原配置文件
6. **测试**: 添加新内容后建议先测试功能是否正常

---

## 常见问题

**Q: 修改后没有生效？**
A: 检查JSON格式是否正确，确保重启了服务器

**Q: 游戏中出现错误？**
A: 检查配置中的ID引用是否正确，确保没有缺少必要字段

**Q: 怪物不会出现？**
A: 检查事件配置中的怪物遭遇配置，确保触发条件正确

**Q: 物品属性不生效？**
A: 检查物品的 `stats` 字段格式，确保属性名称正确
