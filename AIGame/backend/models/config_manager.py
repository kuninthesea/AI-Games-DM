# -*- coding: utf-8 -*-
"""
配置管理器 - 统一管理所有JSON配置文件
"""
import json
import os
from typing import Dict, List, Any, Optional

class ConfigManager:
    def __init__(self, config_dir: str = None):
        """初始化配置管理器"""
        if config_dir is None:
            # 获取当前文件所在目录的父目录，然后添加control_data路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_dir = os.path.join(os.path.dirname(current_dir), 'control_data')
        
        self.config_dir = config_dir
        self._configs = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """加载所有配置文件"""
        config_files = {
            'shops': 'shop_control.json',
            'items': 'item_control.json',
            'locations': 'location_control.json',
            'creatures': 'creature_control.json',
            'skills': 'skill_control.json',
            'events': 'event_control.json'
        }
        
        for config_name, filename in config_files.items():
            filepath = os.path.join(self.config_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self._configs[config_name] = json.load(f)
                print(f"✅ 加载配置文件: {filename}")
            except FileNotFoundError:
                print(f"❌ 配置文件不存在: {filepath}")
                self._configs[config_name] = {}
            except json.JSONDecodeError as e:
                print(f"❌ JSON格式错误 {filename}: {e}")
                self._configs[config_name] = {}
    
    def get_shops(self) -> List[Dict[str, Any]]:
        """获取所有商店配置"""
        return self._configs.get('shops', {}).get('shops', [])
    
    def get_shop_by_name(self, shop_name: str) -> Optional[Dict[str, Any]]:
        """根据商店名称获取商店配置"""
        for shop in self.get_shops():
            if shop.get('shop_name') == shop_name:
                return shop
        return None
    
    def get_items(self) -> List[Dict[str, Any]]:
        """获取所有物品配置"""
        return self._configs.get('items', {}).get('items', [])
    
    def get_item_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """根据物品ID获取物品配置"""
        for item in self.get_items():
            if item.get('item_id') == item_id:
                return item
        return None
    
    def get_areas(self) -> List[Dict[str, Any]]:
        """获取所有区域配置"""
        return self._configs.get('locations', {}).get('areas', [])
    
    def get_area_by_id(self, area_id: str) -> Optional[Dict[str, Any]]:
        """根据区域ID获取区域配置"""
        for area in self.get_areas():
            if area.get('area_id') == area_id:
                return area
        return None
    
    def get_locations(self) -> List[Dict[str, Any]]:
        """获取所有地点配置"""
        return self._configs.get('locations', {}).get('locations', [])
    
    def get_location_by_id(self, location_id: str) -> Optional[Dict[str, Any]]:
        """根据地点ID获取地点配置"""
        for location in self.get_locations():
            if location.get('location_id') == location_id:
                return location
        return None
    
    def get_locations_by_area(self, area_id: str) -> List[Dict[str, Any]]:
        """获取指定区域的所有地点"""
        locations = []
        for location in self.get_locations():
            if location.get('area_id') == area_id:
                locations.append(location)
        return locations
    
    def get_creatures(self) -> List[Dict[str, Any]]:
        """获取所有生物配置"""
        return self._configs.get('creatures', {}).get('creatures', [])
    
    def get_creature_by_id(self, creature_id: str) -> Optional[Dict[str, Any]]:
        """根据生物ID获取生物配置"""
        for creature in self.get_creatures():
            if creature.get('creature_id') == creature_id:
                return creature
        return None
    
    def get_skills(self) -> List[Dict[str, Any]]:
        """获取所有技能配置"""
        return self._configs.get('skills', {}).get('skills', [])
    
    def get_skill_by_id(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """根据技能ID获取技能配置"""
        for skill in self.get_skills():
            if skill.get('skill_id') == skill_id:
                return skill
        return None
    
    def get_events(self) -> List[Dict[str, Any]]:
        """获取所有事件配置"""
        return self._configs.get('events', {}).get('events', [])
    
    def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """根据事件ID获取事件配置"""
        for event in self.get_events():
            if event.get('event_id') == event_id:
                return event
        return None
    
    def get_events_by_location(self, location_id: str) -> List[Dict[str, Any]]:
        """获取指定地点的所有事件"""
        location = self.get_location_by_id(location_id)
        if not location:
            return []
        
        event_ids = location.get('events', [])
        events = []
        for event_id in event_ids:
            event = self.get_event_by_id(event_id)
            if event:
                events.append(event)
        return events
    
    def reload_configs(self):
        """重新加载所有配置文件"""
        self._configs.clear()
        self._load_all_configs()
    
    def get_config_summary(self) -> Dict[str, int]:
        """获取配置摘要信息"""
        return {
            'areas': len(self.get_areas()),
            'locations': len(self.get_locations()),
            'shops': len(self.get_shops()),
            'items': len(self.get_items()),
            'creatures': len(self.get_creatures()),
            'skills': len(self.get_skills()),
            'events': len(self.get_events())
        }

# 创建全局配置管理器实例
config_manager = ConfigManager()

if __name__ == "__main__":
    # 测试配置管理器
    print("=== 配置管理器测试 ===")
    print(f"配置摘要: {config_manager.get_config_summary()}")
    
    # 测试商店配置
    print("\n=== 商店配置 ===")
    for shop in config_manager.get_shops():
        print(f"商店: {shop['display_name']} - 物品数量: {len(shop['items'])}")
    
    # 测试物品配置
    print("\n=== 物品配置 ===")
    sword = config_manager.get_item_by_id('sword_iron')
    if sword:
        print(f"铁剑: {sword['item_name']} - 攻击力: {sword['stats']['attack']}")
    
    # 测试区域配置
    print("\n=== 区域配置 ===")
    for area in config_manager.get_areas():
        locations_in_area = config_manager.get_locations_by_area(area['area_id'])
        print(f"区域: {area['display_name']} - 地点数量: {len(locations_in_area)}")
        for location in locations_in_area:
            print(f"  └─ {location['display_name']} ({location['type']})")
    
    # 测试地点配置
    print("\n=== 地点配置 ===")
    forest = config_manager.get_location_by_id('forest')
    if forest:
        area = config_manager.get_area_by_id(forest['area_id'])
        print(f"森林: {forest['display_name']} - 所属区域: {area['display_name']} - 事件数量: {len(forest['events'])}")
    
    # 测试生物配置
    print("\n=== 生物配置 ===")
    goblin = config_manager.get_creature_by_id('goblin_common_1')
    if goblin:
        print(f"哥布林: {goblin['creature_name']} - 等级: {goblin['level']} - HP: {goblin['base_stats']['hp']}")
