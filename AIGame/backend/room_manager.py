# -*- coding: utf-8 -*-
import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class RoomMessage:
    """房间消息"""
    id: str
    sender: str
    content: str
    message_type: str  # 'private', 'global', 'interaction'
    target_user: Optional[str] = None  # 私聊目标用户
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass 
class RoomUser:
    """房间用户"""
    username: str
    session_token: str
    joined_at: float
    last_activity: float
    is_host: bool = False
    
    def __post_init__(self):
        if not hasattr(self, 'joined_at') or self.joined_at is None:
            self.joined_at = time.time()
        if not hasattr(self, 'last_activity') or self.last_activity is None:
            self.last_activity = time.time()

class GameRoom:
    """游戏房间"""
    def __init__(self, room_id: str, host_username: str):
        self.room_id = room_id
        self.host_username = host_username
        self.users: Dict[str, RoomUser] = {}
        self.messages: List[RoomMessage] = []
        self.created_at = time.time()
        self.host_mode = 'private'  # 'private' 或 'global'
        self.max_users = 10
        
    def add_user(self, username: str, session_token: str) -> bool:
        """添加用户到房间"""
        if len(self.users) >= self.max_users:
            return False
            
        is_host = username == self.host_username
        self.users[username] = RoomUser(
            username=username,
            session_token=session_token,
            joined_at=time.time(),
            last_activity=time.time(),
            is_host=is_host
        )
        return True
    
    def remove_user(self, username: str):
        """从房间移除用户"""
        if username in self.users:
            del self.users[username]
    
    def add_message(self, message: RoomMessage):
        """添加消息到房间"""
        self.messages.append(message)
        
        # 智能模式切换逻辑
        if message.message_type == 'interaction':
            # 互动消息切换为全局模式
            self.host_mode = 'global'
        elif message.sender != "系统" and message.message_type == 'private':
            # 普通私聊消息切换回私聊模式
            self.host_mode = 'private'
        
        # 只保留最近100条消息
        if len(self.messages) > 100:
            self.messages = self.messages[-100:]
    
    def get_messages_for_user(self, username: str, since_timestamp: float = 0) -> List[RoomMessage]:
        """获取用户可见的消息"""
        print(f"获取用户 {username} 的可见消息，时间戳: {since_timestamp}")
        visible_messages = []
        
        for msg in self.messages:
            print(f"检查消息: {msg.sender} -> {msg.content} (类型: {msg.message_type}, 时间戳: {msg.timestamp})")
            
            if msg.timestamp <= since_timestamp:
                print(f"  跳过: 消息时间戳 {msg.timestamp} <= {since_timestamp}")
                continue
                
            # 全局消息所有人都能看到
            if msg.message_type == 'global':
                print(f"  添加全局消息: {msg.content}")
                visible_messages.append(msg)
            # 私聊消息只有发送者和目标用户能看到
            elif msg.message_type == 'private':
                if msg.sender == username or msg.target_user == username:
                    print(f"  添加私聊消息: {msg.content}")
                    visible_messages.append(msg)
                else:
                    print(f"  跳过私聊消息: 不是发送者或接收者")
            # 互动消息所有人都能看到
            elif msg.message_type == 'interaction':
                print(f"  添加互动消息: {msg.content}")
                visible_messages.append(msg)
            else:
                print(f"  未知消息类型: {msg.message_type}")
                
        print(f"最终可见消息数量: {len(visible_messages)}")
        return visible_messages
    
    def update_user_activity(self, username: str):
        """更新用户活动时间"""
        if username in self.users:
            self.users[username].last_activity = time.time()
    
    def is_user_in_room(self, username: str) -> bool:
        """检查用户是否在房间中"""
        return username in self.users
    
    def get_user_list(self) -> List[Dict]:
        """获取房间用户列表"""
        return [
            {
                'username': user.username,
                'is_host': user.is_host,
                'joined_at': user.joined_at,
                'is_online': time.time() - user.last_activity < 30  # 30秒内活跃算在线
            }
            for user in self.users.values()
        ]

class RoomManager:
    """房间管理器"""
    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        
    def create_room(self, host_username: str) -> str:
        """创建房间"""
        room_id = str(uuid.uuid4())[:8]  # 使用短ID
        room = GameRoom(room_id, host_username)
        self.rooms[room_id] = room
        return room_id
    
    def join_room(self, room_id: str, username: str, session_token: str) -> bool:
        """加入房间"""
        if room_id not in self.rooms:
            return False
            
        room = self.rooms[room_id]
        return room.add_user(username, session_token)
    
    def leave_room(self, room_id: str, username: str):
        """离开房间"""
        if room_id in self.rooms:
            room = self.rooms[room_id]
            room.remove_user(username)
            
            # 如果房间为空，删除房间
            if not room.users:
                del self.rooms[room_id]
    
    def get_room(self, room_id: str) -> Optional[GameRoom]:
        """获取房间"""
        return self.rooms.get(room_id)
    
    def send_message(self, room_id: str, sender: str, content: str, 
                    message_type: str = 'private', target_user: str = None) -> bool:
        """发送消息到房间"""
        print(f"RoomManager.send_message: 房间={room_id}, 发送者={sender}, 类型={message_type}")
        
        room = self.get_room(room_id)
        if not room:
            print(f"错误: 房间 {room_id} 不存在")
            return False
        
        # 允许主持人（系统用户）发送消息，或者检查普通用户是否在房间中
        if sender not in ["龙与地下城", "系统"] and not room.is_user_in_room(sender):
            print(f"错误: 用户 {sender} 不在房间中")
            return False
            
        message = RoomMessage(
            id=str(uuid.uuid4()),
            sender=sender,
            content=content,
            message_type=message_type,
            target_user=target_user
        )
        
        print(f"创建消息: {message.content}")
        room.add_message(message)
        room.update_user_activity(sender)
        print(f"消息已添加到房间，当前消息数量: {len(room.messages)}")
        return True
    
    def get_room_list(self) -> List[Dict]:
        """获取房间列表"""
        return [
            {
                'room_id': room_id,
                'host': room.host_username,
                'user_count': len(room.users),
                'max_users': room.max_users,
                'created_at': room.created_at
            }
            for room_id, room in self.rooms.items()
        ]
    
    def cleanup_inactive_rooms(self):
        """清理不活跃的房间"""
        current_time = time.time()
        rooms_to_delete = []
        
        for room_id, room in self.rooms.items():
            # 如果房间空了或者所有用户都超过5分钟不活跃，删除房间
            if not room.users or all(
                current_time - user.last_activity > 300 
                for user in room.users.values()
            ):
                rooms_to_delete.append(room_id)
        
        for room_id in rooms_to_delete:
            del self.rooms[room_id]
