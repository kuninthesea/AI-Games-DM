# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify, session, send_from_directory
import sys
import uuid
import os
from datetime import datetime
from functools import wraps
from api_client import call_ai_api
from user_manager import UserManager
from history_manager import HistoryManager
# from item_manager import ItemManager  # 已替换为配置管理器
from models.config_manager import config_manager
from database import DatabaseManager
from database_separation import db_separation_manager
from room_manager import RoomManager
from models.event import event_manager
from models.skill import skill_manager
from models.creature import creature_manager
from config import DEFAULT_MODEL, game_prompts

sys.stdout.reconfigure(encoding='utf-8')

# Flask应用
app = Flask(__name__)
app.secret_key = 'your-secret-key-here-please-change-in-production'

# 创建管理器实例
user_manager = UserManager()
history_manager = HistoryManager()
# item_manager = ItemManager()  # 已替换为配置管理器
db_manager = db_separation_manager  # 使用数据库分离管理器
room_manager = RoomManager()

# 位置映射配置（全局）
location_mappings = {
    # 英文地点名称映射（直接对应数据库中的location_name）
    'blacksmith': 'blacksmith', 
    'library': 'library',
    'home': 'home',
    'market': 'market',
    'forest': 'forest',
    'village_gate': 'village_gate',
    'forest_clearing': 'forest_clearing',
    # 中文地点名称映射到对应的英文名称
    '家': 'home',
    '家里': 'home',
    '回家': 'home',
    '去家里': 'home',
    '回到家': 'home',
    '铁匠铺': 'blacksmith',
    '去铁匠铺': 'blacksmith',
    '铁匠店': 'blacksmith',
    '图书馆': 'library',
    '去图书馆': 'library',
    '书馆': 'library',
    '市场': 'market',
    '去市场': 'market',
    '集市': 'market',
    '森林': 'forest',
    '村外森林': 'forest',
    '去森林': 'forest',
    '进入森林': 'forest',
    '村庄大门': 'village_gate',
    '大门': 'village_gate',
    '去大门': 'village_gate',
    '村门': 'village_gate',
    '森林空地': 'forest_clearing',
    '空地': 'forest_clearing',
    '去空地': 'forest_clearing',
}

# 加载配置文件
def load_config_files():
    """加载配置文件到应用"""
    try:
        import json
        
        # 加载位置配置
        location_config_path = os.path.join('control_data', 'location_control.json')
        if os.path.exists(location_config_path):
            with open(location_config_path, 'r', encoding='utf-8') as f:
                app.location_data = json.load(f)
                print(f"✅ 已加载位置配置: {len(app.location_data['locations'])} 个位置")
        
        # 加载事件配置
        event_config_path = os.path.join('control_data', 'event_control.json')
        if os.path.exists(event_config_path):
            with open(event_config_path, 'r', encoding='utf-8') as f:
                app.event_data = json.load(f)
                print(f"✅ 已加载事件配置: {len(app.event_data['events'])} 个事件")
                
        # 加载生物配置
        creature_config_path = os.path.join('control_data', 'creature_control.json')
        if os.path.exists(creature_config_path):
            with open(creature_config_path, 'r', encoding='utf-8') as f:
                app.creature_data = json.load(f)
                print(f"✅ 已加载生物配置: {len(app.creature_data['creatures'])} 个生物")
                
    except Exception as e:
        print(f"⚠️ 加载配置文件失败: {e}")

# 在应用启动时加载配置
load_config_files()

def get_creature_data(creature_id):
    """从世界数据库中获取生物数据，转换为战斗用格式"""
    try:
        import sqlite3
        import json
        
        # 连接世界数据库
        world_db_path = os.path.join(os.path.dirname(__file__), 'world_data.db')
        if not os.path.exists(world_db_path):
            print(f"⚠️ 世界数据库不存在: {world_db_path}")
            return None
            
        conn = sqlite3.connect(world_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT creature_name, avatar, base_stats, experience_reward, gold_reward
            FROM creatures 
            WHERE creature_id = ?
        ''', (creature_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            creature_name, avatar, base_stats_json, experience_reward, gold_reward_json = result
            
            # 解析JSON数据
            base_stats = json.loads(base_stats_json) if base_stats_json else {}
            gold_reward = json.loads(gold_reward_json) if gold_reward_json else {}
            
            # 处理金币奖励
            if isinstance(gold_reward, dict):
                gold = gold_reward.get('max', gold_reward.get('min', 5))
            else:
                gold = gold_reward or 0
                
            return {
                'name': creature_name,
                'avatar': avatar or '👹',
                'hp': base_stats.get('hp', 30),
                'maxHp': base_stats.get('hp', 30),
                'attack': base_stats.get('attack', 8),
                'defense': base_stats.get('defense', 3),
                'exp': experience_reward or 15,
                'gold': gold
            }
        
        return None
        
    except Exception as e:
        print(f"❌ 获取生物数据失败: {e}")
        return None

# 添加CORS支持（手动实现）
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Session-Token')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# 认证装饰器
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从请求头获取会话令牌
        session_token = request.headers.get('X-Session-Token')
        if not session_token:
            return jsonify({'success': False, 'error': '缺少会话令牌'}), 401
        
        # 验证会话令牌
        valid, username = user_manager.validate_session(session_token)
        if not valid:
            return jsonify({'success': False, 'error': '会话已过期，请重新登录'}), 401
        
        # 将用户名添加到请求上下文
        request.username = username
        return f(*args, **kwargs)
    return decorated_function

# 应用物品效果
def apply_item_effect(username, effect_str, quantity=1):
    """解析并应用物品效果"""
    try:
        user_data = user_manager.get_user_data(username)
        effect_messages = []
        
        # 解析效果字符串，支持多种格式
        if 'HP+' in effect_str:
            hp_gain = int(effect_str.split('HP+')[1]) * quantity
            old_hp = user_data['HP']
            user_data['HP'] = min(user_data['HP'] + hp_gain, 999)  # 限制最大HP
            actual_gain = user_data['HP'] - old_hp
            effect_messages.append(f"生命值+{actual_gain}")
            
        elif 'MP+' in effect_str:
            mp_gain = int(effect_str.split('MP+')[1]) * quantity
            old_mp = user_data['MP']
            user_data['MP'] = min(user_data['MP'] + mp_gain, 999)  # 限制最大MP
            actual_gain = user_data['MP'] - old_mp
            effect_messages.append(f"魔法值+{actual_gain}")
            
        elif 'gold+' in effect_str or 'Gold+' in effect_str:
            gold_gain = int(effect_str.split('+')[1]) * quantity
            user_data['gold'] += gold_gain
            effect_messages.append(f"金币+{gold_gain}")
        
        # 保存用户数据
        user_manager.save_user_data(username, user_data)
        
        return "，".join(effect_messages) if effect_messages else None
        
    except Exception as e:
        print(f"应用物品效果出错: {e}")
        return None

@app.route('/image/<filename>')
def get_image(filename):
    """提供角色背景图片"""
    try:
        return send_from_directory('../image', filename)
    except FileNotFoundError:
        return '', 404

# 认证相关路由
@app.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'error': '用户名和密码不能为空'})
        
        if len(username) < 2:
            return jsonify({'success': False, 'error': '用户名至少需要2个字符'})
        
        if len(password) < 3:
            return jsonify({'success': False, 'error': '密码至少需要3个字符'})
        
        success, message = user_manager.register_user(username, password)
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'error': '用户名和密码不能为空'})
        
        success, result = user_manager.login_user(username, password)
        
        if success:
            return jsonify({
                'success': True, 
                'message': result['message'],
                'session_token': result['session_token'],
                'username': username
            })
        else:
            return jsonify({'success': False, 'error': result})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/logout', methods=['POST'])
@require_auth
def logout():
    """用户登出"""
    try:
        session_token = request.headers.get('X-Session-Token')
        # 删除会话令牌
        db_manager.execute_query(
            "DELETE FROM user_sessions WHERE session_token = ?",
            (session_token,)
        )
        return jsonify({'success': True, 'message': '登出成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/validate_session', methods=['POST'])
def validate_session():
    """验证会话"""
    try:
        session_token = request.headers.get('X-Session-Token')
        if not session_token:
            return jsonify({'success': False, 'error': '缺少会话令牌'})
        
        valid, username = user_manager.validate_session(session_token)
        
        if valid:
            return jsonify({'success': True, 'username': username})
        else:
            return jsonify({'success': False, 'error': '会话无效'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/chat', methods=['POST'])
@require_auth
def chat():
    """处理聊天请求"""
    try:
        data = request.json
        message = data.get('message', '')
        character = data.get('character', '龙与地下城')
        language = data.get('language', '中文')
        user_identity = data.get('user_identity', '')
        is_regenerate = data.get('regenerate', False)
        username = request.username  # 从认证装饰器获取用户名
        
        # 从数据库加载当前角色的对话历史
        current_messages = history_manager.get_character_history(username, character)
        
        if is_regenerate:
            # 重新生成：不添加新的用户消息，只重新生成最后的AI回复
            if len(current_messages) >= 2 and current_messages[-1]['role'] == 'assistant':
                # 移除最后的AI回复，重新生成
                current_messages.pop()
                temp_messages = current_messages.copy()
            else:
                # 如果没有找到要重新生成的消息，按正常流程处理
                temp_messages = current_messages.copy()
                temp_messages.append({'role': 'user', 'content': message})
        else:
            # 正常聊天：构建消息历史
            temp_messages = current_messages.copy()
            temp_messages.append({'role': 'user', 'content': message})
        
        # 如果没有历史消息，添加系统提示词
        if not temp_messages or temp_messages[0].get('role') != 'system':
            system_prompt = game_prompts.get(character, game_prompts.get('龙与地下城', ''))
            
            # 添加玩家位置信息到系统提示
            location_info = db_manager.get_user_location(username)
            if location_info:
                location_context = (f'\n\n【当前状态】玩家{username}现在位于：{location_info["area_display_name"]} - {location_info["location_display_name"]}'
                                  f'（{location_info["description"]}）')
                system_prompt += location_context
            
            if system_prompt:
                temp_messages.insert(0, {'role': 'system', 'content': system_prompt})
        
        # 调用AI API
        reply = call_ai_api(DEFAULT_MODEL, temp_messages)
        
        # 检查AI回复中是否包含移动指令（支持带**的格式）
        if reply and 'MOVE_TO:' in reply:
            # 提取移动目标（处理带**的格式）
            import re
            move_pattern = r'\*?\*?MOVE_TO:([^\*\s]+)\*?\*?'
            match = re.search(move_pattern, reply)
            if match:
                target_location = match.group(1).strip()
                
                # 检查是否是有效地点
                if target_location in location_mappings:
                    actual_location = location_mappings[target_location]
                    success, message = db_manager.update_user_location(username, actual_location)
                    if success:
                        print(f"✅ 玩家 {username} 移动到了 {actual_location}")
                        
                        # 检查是否触发特定位置事件
                        if actual_location == 'forest':
                            # 触发村外森林的哥布林战斗事件
                            user_data = user_manager.get_user_data(username)
                            if user_data:
                                battle_event = {
                                    'type': 'battle',
                                    'location': 'forest',
                                    'enemy': 'goblin',
                                    'message': '你在村外森林遭遇了一只普通哥布林！'
                                }
                                reply += f"\n\n【战斗触发】{battle_event['message']}"
                        
                        # 从回复中移除移动指令（支持带**的格式）
                        reply = re.sub(r'\*?\*?MOVE_TO:[^\*\s]+\*?\*?', '', reply).strip()
                    else:
                        print(f"❌ 玩家移动失败: {message}")
                else:
                    print(f"❌ 无效的移动目标: {target_location}")
            else:
                print("❌ 无法解析移动指令")
        
        if is_regenerate:
            # 重新生成：只保存AI回复
            history_manager.save_message(username, character, 'assistant', reply)
        else:
            # 正常聊天：保存用户消息和AI回复
            history_manager.save_message(username, character, 'user', message)
            history_manager.save_message(username, character, 'assistant', reply)
        
        return jsonify({'success': True, 'response': reply, 'reply': reply})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_character_history', methods=['POST'])
@require_auth
def get_character_history():
    """获取指定角色的聊天历史"""
    try:
        data = request.json
        character = data.get('character', '龙与地下城')
        username = request.username
        
        # 从数据库加载角色的对话历史
        messages = history_manager.get_character_history(username, character)
        
        return jsonify({
            'success': True,
            'messages': messages,
            'username': username
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/clear', methods=['POST'])
@require_auth
def clear_history():
    """清除聊天历史"""
    try:
        data = request.json
        character = data.get('character', '龙与地下城')
        username = request.username
        
        success = history_manager.clear_character_history(username, character)
        
        if success:
            return jsonify({'success': True, 'message': '历史记录已清除'})
        else:
            return jsonify({'success': False, 'error': '清除历史记录失败'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_user_data', methods=['POST'])
@require_auth
def get_user_data():
    """获取用户数据"""
    try:
        username = request.username
        user_data = user_manager.get_user_data(username)
        return jsonify({'success': True, 'data': user_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/update_user_stats', methods=['POST'])
@require_auth
def update_user_stats():
    """更新用户属性"""
    try:
        data = request.json
        username = request.username
        
        user_data = user_manager.get_user_data(username)
        
        # 更新基础属性
        if 'HP' in data:
            user_data['HP'] = max(0, data['HP'])
        if 'MP' in data:
            user_data['MP'] = max(0, data['MP'])
        if 'gold' in data:
            user_data['gold'] = max(0, data['gold'])
        
        # 更新新属性
        if 'experience' in data:
            user_data['experience'] = max(0, data['experience'])
        if 'level' in data:
            user_data['level'] = max(1, data['level'])
        if 'attack' in data:
            user_data['attack'] = max(0, data['attack'])
        if 'defense' in data:
            user_data['defense'] = max(0, data['defense'])
        if 'critical_rate' in data:
            user_data['critical_rate'] = max(0, min(100, data['critical_rate']))  # 限制在0-100%之间
        if 'critical_damage' in data:
            user_data['critical_damage'] = max(100, data['critical_damage'])  # 最小100%（即无额外伤害）
        
        success = user_manager.save_user_data(username, user_data)
        
        if success:
            return jsonify({'success': True, 'data': user_data})
        else:
            return jsonify({'success': False, 'error': '保存用户数据失败'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_characters', methods=['GET'])
def get_characters():
    """获取所有角色配置"""
    return jsonify({'success': True, 'characters': game_prompts})

@app.route('/get_items', methods=['GET'])
def get_items():
    """获取所有物品"""
    try:
        items = config_manager.get_items()
        return jsonify({'success': True, 'items': items})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/search_items', methods=['POST'])
def search_items():
    """搜索物品"""
    try:
        data = request.json
        query = data.get('query', '')
        main_type = data.get('main_type', '')
        sub_type = data.get('sub_type', '')
        rarity = data.get('rarity', '')
        
        # 简化版搜索 - 返回所有物品，前端可以过滤
        items = config_manager.get_items()
        # TODO: 实现服务器端物品搜索过滤
        return jsonify({'success': True, 'items': items})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/add_item', methods=['POST'])
@require_auth
def add_item():
    """向背包添加物品"""
    try:
        data = request.json
        username = request.username
        item_id = data.get('item_id', '')
        quantity = data.get('quantity', 1)
        
        if not item_id:
            return jsonify({'success': False, 'error': '物品ID不能为空'})
        
        # 验证物品是否存在
        item = config_manager.get_item_by_id(item_id)
        if not item:
            return jsonify({'success': False, 'error': '物品不存在'})
        
        success = user_manager.add_item_to_inventory(username, item_id, quantity)
        
        if success:
            return jsonify({'success': True, 'message': f'成功添加 {item["name"]} x{quantity}'})
        else:
            return jsonify({'success': False, 'error': '添加物品失败'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/use_item', methods=['POST'])
@require_auth
def use_item():
    """使用物品"""
    try:
        data = request.json
        username = request.username
        item_id = data.get('item_id', '')
        quantity = data.get('quantity', 1)
        
        if not item_id:
            return jsonify({'success': False, 'error': '物品ID不能为空'})
        
        # 获取物品信息
        item = config_manager.get_item_by_id(item_id)
        if not item:
            return jsonify({'success': False, 'error': '物品不存在'})
        
        # 检查背包中是否有足够的物品
        user_data = user_manager.get_user_data(username)
        has_enough = False
        for inv_item in user_data['inventory']['items']:
            if inv_item['id'] == item_id and inv_item['quantity'] >= quantity:
                has_enough = True
                break
        
        if not has_enough:
            return jsonify({'success': False, 'error': '背包中没有足够的物品'})
        
        # 移除物品
        user_manager.remove_item_from_inventory(username, item_id, quantity)
        
        # 应用物品效果
        effect_result = f"使用了 {item['name']} x{quantity}"
        
        # 解析和应用效果
        if item.get('effect'):
            effect_applied = apply_item_effect(username, item['effect'], quantity)
            if effect_applied:
                effect_result += f"，{effect_applied}"
            else:
                effect_result += f"，效果：{item['effect']}"
        
        return jsonify({'success': True, 'message': effect_result})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/equip_item', methods=['POST'])
@require_auth
def equip_item():
    """装备物品"""
    try:
        data = request.json
        username = request.username
        item_id = data.get('item_id', '')
        slot = data.get('slot', '')
        
        if not item_id or not slot:
            return jsonify({'success': False, 'error': '物品ID和装备槽位不能为空'})
        
        success, message = user_manager.equip_item(username, item_id, slot)
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/unequip_item', methods=['POST'])
@require_auth
def unequip_item():
    """卸下装备"""
    try:
        data = request.json
        username = request.username
        slot = data.get('slot', '')
        
        if not slot:
            return jsonify({'success': False, 'error': '装备槽位不能为空'})
        
        success, message = user_manager.unequip_item(username, slot)
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ===== 联机功能 API =====

@app.route('/create_room', methods=['POST'])
@require_auth
def create_room():
    """创建游戏房间"""
    try:
        username = request.username
        room_id = room_manager.create_room(username)
        
        # 将创建者加入房间
        success = room_manager.join_room(room_id, username, request.headers.get('X-Session-Token'))
        
        if success:
            return jsonify({
                'success': True, 
                'room_id': room_id,
                'message': f'房间 {room_id} 创建成功！'
            })
        else:
            return jsonify({'success': False, 'error': '创建房间失败'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/join_room', methods=['POST'])
@require_auth
def join_room():
    """加入游戏房间"""
    try:
        data = request.json
        username = request.username
        room_id = data.get('room_id', '').strip()
        
        if not room_id:
            return jsonify({'success': False, 'error': '房间ID不能为空'})
        
        success = room_manager.join_room(room_id, username, request.headers.get('X-Session-Token'))
        
        if success:
            return jsonify({
                'success': True,
                'message': f'成功加入房间 {room_id}！'
            })
        else:
            return jsonify({'success': False, 'error': '加入房间失败，房间可能不存在或已满'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/leave_room', methods=['POST'])
@require_auth
def leave_room():
    """离开游戏房间"""
    try:
        data = request.json
        username = request.username
        room_id = data.get('room_id', '')
        
        room_manager.leave_room(room_id, username)
        
        return jsonify({
            'success': True,
            'message': '已离开房间'
        })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_room_list', methods=['GET'])
def get_room_list():
    """获取房间列表"""
    try:
        # 清理不活跃的房间
        room_manager.cleanup_inactive_rooms()
        
        rooms = room_manager.get_room_list()
        return jsonify({'success': True, 'rooms': rooms})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_room_info', methods=['POST'])
@require_auth
def get_room_info():
    """获取房间信息"""
    try:
        data = request.json
        room_id = data.get('room_id', '')
        
        room = room_manager.get_room(room_id)
        if not room:
            return jsonify({'success': False, 'error': '房间不存在'})
        
        return jsonify({
            'success': True,
            'room_info': {
                'room_id': room.room_id,
                'host': room.host_username,
                'host_mode': room.host_mode,
                'users': room.get_user_list(),
                'user_count': len(room.users),
                'max_users': room.max_users
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/send_room_message', methods=['POST'])
@require_auth
def send_room_message():
    """发送房间消息"""
    print(f"\n=== 收到房间消息请求 ===")
    print(f"请求方法: {request.method}")
    print(f"请求URL: {request.url}")
    try:
        data = request.json
        print(f"请求数据: {data}")
        if not data:
            print("❌ 请求数据为空!")
        username = request.username
        room_id = data.get('room_id', '')
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'private')  # private, global, interaction
        target_user = data.get('target_user', '')
        
        print(f"=== 发送房间消息 ===")
        print(f"用户: {username}")
        print(f"房间ID: {room_id}")
        print(f"消息类型: {message_type}")
        print(f"目标用户: {target_user}")
        print(f"消息内容: {content}")
        
        if not room_id or not content:
            return jsonify({'success': False, 'error': '房间ID和消息内容不能为空'})
        
        room = room_manager.get_room(room_id)
        if not room:
            return jsonify({'success': False, 'error': '房间不存在'})
        
        if not room.is_user_in_room(username):
            return jsonify({'success': False, 'error': '您不在此房间中'})
        
        # 处理互动消息 - 只发送互动消息，主持人回应由单独的API处理
        if message_type == 'interaction' and target_user:
            print(f"处理互动消息: {username} -> {target_user}")
            # 切换房间为全局模式
            room.host_mode = 'global'
            print(f"房间模式切换为: {room.host_mode}")
            
            # 发送原始互动消息
            success = room_manager.send_message(room_id, username, content, message_type, target_user)
            if not success:
                print(f"发送互动消息失败")
                return jsonify({'success': False, 'error': '发送互动消息失败'})
            
            print(f"互动消息发送完成，主持人回应将由单独API处理")
        else:
            # 非互动消息，确保使用私聊模式
            if message_type != 'global':
                room.host_mode = 'private'
            
            success = room_manager.send_message(room_id, username, content, message_type, target_user)
            if not success:
                return jsonify({'success': False, 'error': '发送消息失败'})
        
        return jsonify({'success': True, 'message': '消息发送成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/trigger_dm_response', methods=['POST'])
@require_auth
def trigger_dm_response():
    """触发主持人回应"""
    print(f"\n=== 触发主持人回应 ===")
    try:
        data = request.json
        username = request.username
        room_id = data.get('room_id', '')
        interaction_content = data.get('interaction_content', '')
        original_sender = data.get('original_sender', '')
        target_user = data.get('target_user', '')
        
        print(f"房间ID: {room_id}")
        print(f"互动内容: {interaction_content}")
        print(f"原发送者: {original_sender}")
        print(f"目标用户: {target_user}")
        
        if not room_id or not interaction_content:
            return jsonify({'success': False, 'error': '缺少必要参数'})
        
        room = room_manager.get_room(room_id)
        if not room:
            return jsonify({'success': False, 'error': '房间不存在'})
        
        # 创建智能的主持人回应
        try:
            # 获取龙与地下城角色的系统提示词
            system_prompt = game_prompts.get('龙与地下城', '')
            
            # 构建消息历史
            temp_messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': interaction_content}
            ]
            
            print(f"正在生成AI回应...")
            dm_reply = call_ai_api(DEFAULT_MODEL, temp_messages)
            
            if not dm_reply or dm_reply.strip() == "":
                dm_reply = f"🎲 主持人注意到了这个互动并点了点头..."
                print(f"AI回应为空，使用默认回应")
            else:
                print(f"AI回应生成成功，长度: {len(dm_reply)}")
                
        except Exception as e:
            print(f"AI回应生成失败: {e}")
            dm_reply = f"🎲 主持人注意到了这个互动：{interaction_content}"
        
        print(f"最终主持人回应: {dm_reply[:100]}...")
        
        # 发送主持人回应
        import time
        time.sleep(0.1)  # 确保时间戳不同
        
        send_result = room_manager.send_message(room_id, "龙与地下城", dm_reply, 'global')
        print(f"主持人回应发送结果: {send_result}")
        
        if send_result:
            return jsonify({'success': True, 'message': '主持人回应已发送'})
        else:
            return jsonify({'success': False, 'error': '主持人回应发送失败'})
            
    except Exception as e:
        print(f"❌ 触发主持人回应出错: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_room_messages', methods=['POST'])
@require_auth
def get_room_messages():
    """获取房间消息"""
    try:
        data = request.json
        username = request.username
        room_id = data.get('room_id', '')
        since_timestamp = data.get('since_timestamp', 0)
        
        print(f"=== 获取房间消息 ===")
        print(f"用户: {username}")
        print(f"房间ID: {room_id}")
        print(f"时间戳: {since_timestamp}")
        
        room = room_manager.get_room(room_id)
        if not room:
            print(f"错误: 房间 {room_id} 不存在")
            return jsonify({'success': False, 'error': '房间不存在'})
        
        print(f"房间总消息数量: {len(room.messages)}")
        for i, msg in enumerate(room.messages):
            print(f"消息 {i}: {msg.sender} -> {msg.content} (类型: {msg.message_type}, 时间戳: {msg.timestamp})")
        
        if not room.is_user_in_room(username):
            print(f"错误: 用户 {username} 不在房间中")
            return jsonify({'success': False, 'error': '您不在此房间中'})
        
        # 更新用户活动时间
        room.update_user_activity(username)
        
        messages = room.get_messages_for_user(username, since_timestamp)
        print(f"用户可见消息数量: {len(messages)}")
        
        # 转换消息格式
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'id': msg.id,
                'sender': msg.sender,
                'content': msg.content,
                'message_type': msg.message_type,
                'target_user': msg.target_user,
                'timestamp': msg.timestamp
            })
        
        return jsonify({
            'success': True,
            'messages': formatted_messages,
            'room_info': {
                'host_mode': room.host_mode,
                'users': room.get_user_list()
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/set_host_mode', methods=['POST'])
@require_auth
def set_host_mode():
    """设置主持人模式"""
    try:
        data = request.json
        username = request.username
        room_id = data.get('room_id', '')
        host_mode = data.get('host_mode', 'private')  # private 或 global
        
        room = room_manager.get_room(room_id)
        if not room:
            return jsonify({'success': False, 'error': '房间不存在'})
        
        if room.host_username != username:
            return jsonify({'success': False, 'error': '只有房主可以设置模式'})
        
        room.host_mode = host_mode
        
        return jsonify({
            'success': True,
            'message': f'主持人模式已设置为: {"全局模式" if host_mode == "global" else "私聊模式"}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
# ======= 地图系统 API =======
@app.route('/get_user_location', methods=['GET'])
@require_auth
def get_user_location():
    """获取用户当前位置"""
    try:
        username = request.username
        location_data = db_manager.get_user_location(username)
        
        if location_data:
            return jsonify({
                'success': True,
                'location': location_data
            })
        else:
            # 为新用户初始化位置
            db_manager.initialize_user_location(username)
            location_data = db_manager.get_user_location(username)
            return jsonify({
                'success': True,
                'location': location_data
            })
            
    except Exception as e:
        print(f"获取用户位置出错: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_area_locations', methods=['GET'])
@require_auth
def get_area_locations():
    """获取区域内的所有地点"""
    try:
        username = request.username
        area_name = request.args.get('area', 'novice_village')
        
        locations = db_manager.get_area_locations(area_name)
        
        return jsonify({
            'success': True,
            'area_name': area_name,
            'locations': locations
        })
        
    except Exception as e:
        print(f"获取区域地点出错: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/move_to_location', methods=['POST'])
@require_auth
def move_to_location():
    """移动到指定地点"""
    try:
        data = request.json
        username = request.username
        target_location = data.get('location')
        
        if not target_location:
            return jsonify({'success': False, 'error': '缺少目标位置'})
        
        success, message = db_manager.update_user_location(username, target_location)
        
        if success:
            # 获取新位置信息
            location_data = db_manager.get_user_location(username)
            return jsonify({
                'success': True,
                'message': message,
                'location': location_data
            })
        else:
            return jsonify({'success': False, 'error': message})
            
    except Exception as e:
        print(f"移动位置出错: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_location_info', methods=['GET'])
@require_auth  
def get_location_info():
    """获取指定位置的详细信息"""
    try:
        location_name = request.args.get('location')
        if not location_name:
            return jsonify({'success': False, 'error': '缺少位置参数'})
            
        # 在位置映射中查找位置
        location_id = location_mappings.get(location_name, location_name)
        
        # 从配置文件中获取位置信息
        if hasattr(app, 'location_data'):
            for location in app.location_data['locations']:
                if location['location_id'] == location_id or location['location_name'] == location_name:
                    return jsonify({
                        'success': True,
                        'location': location
                    })
        
        return jsonify({'success': False, 'error': '未找到位置信息'})
        
    except Exception as e:
        print(f"获取位置信息出错: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/trigger_event', methods=['POST'])
@require_auth
def trigger_interaction_event():
    """触发位置互动事件"""
    try:
        data = request.json
        username = request.username
        event_id = data.get('event_id')
        
        if not event_id:
            return jsonify({'success': False, 'error': '缺少事件ID'})
        
        # 获取事件配置
        if hasattr(app, 'event_data'):
            event_config = None
            for event in app.event_data['events']:
                if event['event_id'] == event_id:
                    event_config = event
                    break
                    
            if not event_config:
                return jsonify({'success': False, 'error': '未找到指定事件'})
                
            # 统一处理所有事件类型，完全基于JSON配置
            event_type = event_config['event_type']
            event_data = event_config.get('event_data', {})
            event_name = event_config['event_name']
            
            # 构建基础响应
            response_data = {
                'success': True,
                'message': event_config.get('description', f'触发了{event_name}'),
                'event_type': event_type,
                'event_id': event_id
            }
            
            # 根据事件类型添加特定数据
            if event_type == 'fight':
                # 战斗事件 - 从配置中获取生物数据
                creatures = event_data.get('creatures', [])
                if creatures:
                    # 随机选择一个生物（基于生成概率）
                    import random
                    creature_choice = None
                    for creature in creatures:
                        if random.random() <= creature.get('spawn_chance', 1.0):
                            creature_choice = creature
                            break
                    
                    if creature_choice:
                        # 从生物配置中获取详细数据
                        creature_id = creature_choice['creature_id']
                        creature_data = get_creature_data(creature_id)
                        
                        if creature_data:
                            response_data.update({
                                'battle_started': True,
                                'battle_type': event_data.get('battle_type', 'creature'),
                                'safe_battle': event_data.get('safe_battle', False),
                                'flee_allowed': event_data.get('flee_allowed', True),
                                'enemy': creature_data
                            })
                        else:
                            response_data['message'] = f'无法找到生物数据: {creature_id}'
                    else:
                        response_data['message'] = '没有生物出现'
                else:
                    response_data['message'] = '事件配置中没有生物数据'
            
            elif event_type == 'shop':
                # 商店事件
                response_data.update({
                    'shop_opened': True,
                    'shop_type': event_data.get('shop_type', 'general'),
                    'shop_id': event_data.get('shop_id', 'unknown'),
                    'auto_open_shop': event_data.get('auto_open_shop', False)
                })
                
            elif event_type == 'healing':
                # 恢复事件
                response_data.update({
                    'healing_triggered': True,
                    'heal_percentage': event_data.get('heal_percentage', 1.0),
                    'restore_mp_percentage': event_data.get('restore_mp_percentage', 1.0)
                })
                
            elif event_type == 'gathering':
                # 采集事件
                response_data.update({
                    'gathering_started': True,
                    'gathering_type': event_data.get('gathering_type', 'general'),
                    'success_chance': event_data.get('success_chance', 0.8),
                    'items': event_data.get('items', [])
                })
                
            elif event_type == 'repair':
                # 修理事件
                response_data.update({
                    'repair_started': True,
                    'repair_cost_multiplier': event_data.get('repair_cost_multiplier', 0.1)
                })
                
            elif event_type == 'research':
                # 研究事件
                response_data.update({
                    'research_started': True,
                    'research_type': event_data.get('research_type', 'general')
                })
                
            elif event_type == 'treasure':
                # 宝藏事件
                response_data.update({
                    'treasure_found': True,
                    'treasure_type': event_data.get('treasure_type', 'item'),
                    'items': event_data.get('items', []),
                    'gold_reward': event_data.get('gold_reward', {})
                })
            
            return jsonify(response_data)
        else:
            return jsonify({'success': False, 'error': '事件系统未初始化'})
        
    except Exception as e:
        print(f"触发事件出错: {e}")
        return jsonify({'success': False, 'error': str(e)})

# ======= 商店系统 API =======
@app.route('/get_current_shop', methods=['GET'])
@require_auth
def get_current_shop():
    """获取当前位置的商店信息"""
    try:
        username = request.username
        print(f"🔍 检查用户商店 - 用户: {username}")
        
        location_data = db_manager.get_user_location(username)
        print(f"📍 用户位置数据: {location_data}")
        
        if not location_data:
            print("❌ 无法获取用户位置")
            return jsonify({'success': False, 'error': '无法获取用户位置'})
        
        current_location = location_data['current_location']
        print(f"🗺️ 当前位置: {current_location}")
        
        shop_data = db_manager.get_shop_by_location(current_location)
        print(f"🏪 商店数据: {shop_data}")
        
        if shop_data:
            print(f"✅ 找到商店: {shop_data['display_name']}")
            return jsonify({
                'success': True,
                'shop': shop_data,
                'location': location_data
            })
        else:
            print(f"🚫 位置 {current_location} 没有商店")
            return jsonify({
                'success': False,
                'error': '当前位置没有商店'
            })
            
    except Exception as e:
        print(f"❌ 获取商店信息出错: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_shop_items', methods=['GET'])
@require_auth
def get_shop_items():
    """获取商店商品列表"""
    try:
        username = request.username
        shop_name = request.args.get('shop_name')
        
        print(f"🛒 获取商店商品 - 用户: {username}, 商店: {shop_name}")
        
        if not shop_name:
            print("❌ 缺少商店名称")
            return jsonify({'success': False, 'error': '缺少商店名称'})
        
        items = db_manager.get_shop_items(shop_name)
        print(f"📦 数据库商品数量: {len(items) if items else 0}")
        print(f"📦 数据库原始商品: {items}")
        
        # 从配置文件获取物品详细信息
        item_details = []
        for item in items:
            print(f"🔍 处理商品: {item['item_id']}")
            item_info = config_manager.get_item_by_id(item['item_id'])
            print(f"📋 商品详情: {item_info}")
            
            if item_info:
                item_detail = {
                    'id': item['item_id'],
                    'name': item_info.get('item_name', item['item_id']),
                    'description': item_info.get('description', ''),
                    'type': item_info.get('item_type', ''),
                    'sub_type': item_info.get('item_type', ''),  # 使用item_type作为sub_type
                    'rarity': item_info.get('rarity', 'common'),
                    'price': item['price'],
                    'stock': item['stock'],
                    'is_available': item['is_available']
                }
                item_details.append(item_detail)
                print(f"✅ 添加商品详情: {item_detail}")
            else:
                print(f"⚠️ 商品 {item['item_id']} 未在配置文件中找到")
        
        print(f"🎯 最终商品列表: {len(item_details)} 个")
        return jsonify({
            'success': True,
            'items': item_details
        })
        
    except Exception as e:
        print(f"❌ 获取商店商品出错: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/purchase_item', methods=['POST'])
@require_auth
def purchase_item():
    """购买商品"""
    try:
        data = request.json
        username = request.username
        shop_name = data.get('shop_name')
        item_id = data.get('item_id')
        price = data.get('price')
        
        if not all([shop_name, item_id, price]):
            return jsonify({'success': False, 'error': '缺少必要参数'})
        
        success, message = db_manager.purchase_item(username, shop_name, item_id, price)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            })
            
    except Exception as e:
        print(f"购买商品出错: {e}")
        return jsonify({'success': False, 'error': str(e)})

# ===== 事件相关API =====

@app.route('/api/events/check', methods=['POST'])
@require_auth
def check_events():
    """检查可触发的事件"""
    try:
        username = request.username
        user_data = user_manager.get_user_data(username)
        if not user_data:
            return jsonify({'success': False, 'error': '用户不存在'}), 404
        
        # 获取用户上下文
        user_context = {
            'user_id': username,  # 使用 username 作为 user_id
            'username': username,
            'location': user_data.get('current_room', ''),
            'level': user_data.get('level', 1),
            'hp': user_data.get('HP', 100)  # 注意这里是大写的 HP
        }
        
        # 检查可触发的事件
        available_events = event_manager.check_event_conditions(user_context)
        
        # 转换为字典格式
        events_data = [event.to_dict() for event in available_events]
        
        return jsonify({
            'success': True,
            'events': events_data,
            'count': len(events_data)
        })
    
    except Exception as e:
        print(f"检查事件时出错: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/events/trigger/<int:event_id>', methods=['POST'])
@require_auth
def trigger_event(event_id):
    """触发指定事件"""
    try:
        username = request.username
        user_data = user_manager.get_user_data(username)
        if not user_data:
            return jsonify({'success': False, 'error': '用户不存在'}), 404
        
        # 触发事件
        result = event_manager.trigger_event(event_id, username)
        
        return jsonify(result)
    
    except Exception as e:
        print(f"触发事件时出错: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/events/history', methods=['GET'])
@require_auth
def get_event_history():
    """获取用户事件历史"""
    try:
        username = request.username
        user_data = user_manager.get_user_data(username)
        if not user_data:
            return jsonify({'success': False, 'error': '用户不存在'}), 404
        
        limit = request.args.get('limit', 10, type=int)
        history = event_manager.get_event_history(username, limit)
        
        return jsonify({
            'success': True,
            'history': history
        })
    
    except Exception as e:
        print(f"获取事件历史时出错: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/events/all', methods=['GET'])
@require_auth
def get_all_events():
    """获取所有事件（管理用）"""
    try:
        events = event_manager.get_all_active_events()
        events_data = [event.to_dict() for event in events]
        
        return jsonify({
            'success': True,
            'events': events_data
        })
    
    except Exception as e:
        print(f"获取所有事件时出错: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/events/battle/<int:event_id>', methods=['POST'])
@require_auth
def start_battle_from_event(event_id):
    """从事件开始战斗"""
    try:
        username = request.username
        user_data = user_manager.get_user_data(username)
        if not user_data:
            return jsonify({'success': False, 'error': '用户不存在'}), 404
        
        # 获取事件信息
        event = event_manager.get_event(event_id)
        if not event or event.event_type != 'battle':
            return jsonify({'success': False, 'error': '无效的战斗事件'}), 400
        
        # 触发事件并获取敌人数据
        trigger_result = event_manager.trigger_event(event_id, username)
        
        if not trigger_result['success']:
            return jsonify(trigger_result)
        
        # 返回战斗数据
        return jsonify({
            'success': True,
            'battle_data': trigger_result['result'],
            'event_name': event.name
        })
    
    except Exception as e:
        print(f"从事件开始战斗时出错: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== 技能相关API =====

@app.route('/api/skills', methods=['GET'])
@require_auth
def get_all_skills():
    """获取所有技能"""
    try:
        skills = skill_manager.get_all_skills()
        skills_data = [skill.to_dict() for skill in skills]
        
        return jsonify({
            'success': True,
            'skills': skills_data
        })
    
    except Exception as e:
        print(f"获取技能列表时出错: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/skills/<int:skill_id>', methods=['GET'])
@require_auth
def get_skill(skill_id):
    """获取指定技能"""
    try:
        skill = skill_manager.get_skill(skill_id)
        if not skill:
            return jsonify({'success': False, 'error': '技能不存在'}), 404
        
        return jsonify({
            'success': True,
            'skill': skill.to_dict()
        })
    
    except Exception as e:
        print(f"获取技能时出错: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== 生物相关API =====

@app.route('/api/creatures', methods=['GET'])
@require_auth
def get_all_creatures():
    """获取所有生物"""
    try:
        quality = request.args.get('quality')  # 可选的品质过滤
        
        if quality:
            creatures = creature_manager.get_creatures_by_quality(quality)
        else:
            creatures = creature_manager.get_all_creatures()
        
        creatures_data = []
        for creature in creatures:
            creature_dict = creature.to_dict()
            creature_dict['effective_attack'] = creature.get_effective_attack()
            creature_dict['effective_hp'] = creature.get_effective_hp()
            creature_dict['quality_multiplier'] = creature.get_quality_multiplier()
            creatures_data.append(creature_dict)
        
        return jsonify({
            'success': True,
            'creatures': creatures_data
        })
    
    except Exception as e:
        print(f"获取生物列表时出错: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/creatures/<int:creature_id>', methods=['GET'])
@require_auth
def get_creature(creature_id):
    """获取指定生物"""
    try:
        creature = creature_manager.get_creature(creature_id)
        if not creature:
            return jsonify({'success': False, 'error': '生物不存在'}), 404
        
        creature_dict = creature.to_dict()
        creature_dict['effective_attack'] = creature.get_effective_attack()
        creature_dict['effective_hp'] = creature.get_effective_hp()
        creature_dict['quality_multiplier'] = creature.get_quality_multiplier()
        creature_dict['skill_objects'] = [skill.to_dict() for skill in creature.get_skill_objects()]
        
        return jsonify({
            'success': True,
            'creature': creature_dict
        })
    
    except Exception as e:
        print(f"获取生物时出错: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/creatures/<int:creature_id>/battle', methods=['GET'])
@require_auth
def create_battle_instance(creature_id):
    """创建生物的战斗实例"""
    try:
        level_modifier = request.args.get('level', 1.0, type=float)
        
        battle_instance = creature_manager.create_battle_instance(creature_id, level_modifier)
        if not battle_instance:
            return jsonify({'success': False, 'error': '生物不存在'}), 404
        
        return jsonify({
            'success': True,
            'battle_instance': battle_instance
        })
    
    except Exception as e:
        print(f"创建战斗实例时出错: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test/battle-goblin', methods=['POST'])
@require_auth
def test_battle_goblin():
    """测试与哥布林的战斗"""
    try:
        goblin = creature_manager.get_creature_by_name("普通哥布林")
        if not goblin:
            return jsonify({'success': False, 'error': '找不到普通哥布林'}), 404
        
        battle_instance = creature_manager.create_battle_instance(goblin.creature_id)
        
        return jsonify({
            'success': True,
            'message': '开始与普通哥布林的战斗！',
            'battle_data': {
                'enemy': battle_instance
            }
        })
    
    except Exception as e:
        print(f"测试哥布林战斗时出错: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/api/training/dummy-battle', methods=['POST'])
@require_auth
def start_training_dummy_battle():
    """在家里与木偶假人战斗"""
    try:
        username = request.username
        user_data = user_manager.get_user_data(username)
        if not user_data:
            return jsonify({'success': False, 'error': '用户不存在'}), 404
        
        # 检查用户是否在家
        location_data = db_manager.get_user_location(username)
        if not location_data or location_data['current_location'] != 'home':
            return jsonify({'success': False, 'error': '只有在家里才能与木偶假人战斗'}), 400
        
        # 获取木偶假人并创建战斗实例
        training_dummy = creature_manager.get_creature_by_name("木偶假人")
        if not training_dummy:
            return jsonify({'success': False, 'error': '找不到木偶假人'}), 404
        
        # 创建战斗实例
        battle_instance = creature_manager.create_battle_instance(training_dummy.creature_id, 1.0)
        
        return jsonify({
            'success': True,
            'message': '开始与木偶假人的训练战斗！',
            'battle_triggered': True,
            'battle_data': {
                'enemy': battle_instance,
                'event_type': 'training_battle',
                'location': 'home'
            }
        })
    
    except Exception as e:
        print(f"开始假人战斗时出错: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("服务器启动在端口 5000 (可远程访问)")
    app.run(host='0.0.0.0', port=5000, debug=False)
