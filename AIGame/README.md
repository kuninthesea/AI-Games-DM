# TRPG跑团游戏助手 v2.0

一个基于Flask的TRPG（桌面角色扮演游戏）助手，采用前后端分离架构。

## 项目结构

```
AIGame/
├── backend/                 # 后端服务
│   ├── app.py              # 主应用文件
│   ├── config.py           # 配置文件
│   ├── api_client.py       # AI API客户端
│   ├── user_manager.py     # 用户管理模块
│   └── history_manager.py  # 历史记录管理模块
├── frontend/               # 前端服务
│   ├── app.py             # 前端服务器
│   ├── templates/         # HTML模板
│   │   └── index.html     # 主页面
│   └── static/            # 静态资源
│       ├── css/
│       │   └── style.css  # 样式文件
│       └── js/
│           └── app.js     # 应用逻辑
├── history/               # 聊天历史文件
├── userdata/             # 用户数据文件
├── image/                # 角色图片
├── start.bat             # 启动脚本
└── README.md            # 项目说明
```

## 功能特性

- 🎭 多角色AI对话系统
- 👤 用户注册/登录系统
- 📊 角色数据管理 (HP/MP/金币)
- 💬 聊天历史记录
- 🖼️ 角色图片显示
- 🔄 消息重新生成和编辑
- 💾 数据持久化存储

## 安装依赖

```bash
pip install flask openai google-generativeai flask-cors
```

## 启动方式

### 方法1: 使用启动脚本（推荐）
双击运行 `start.bat` 文件

### 方法2: 手动启动

1. 启动后端服务器：
```bash
cd backend
python app.py
```

2. 启动前端服务器：
```bash
cd frontend
python app.py
```

## 访问地址

- 前端界面: http://localhost:3000
- 后端API: http://localhost:5000

## 配置说明

在 `backend/config.py` 中配置您的API密钥：

```python
OPENAI_API_KEY = "your-openai-api-key"
GEMINI_API_KEY = "your-gemini-api-key"
```

## API接口

### 用户管理
- `POST /login` - 用户登录
- `POST /register` - 用户注册
- `POST /get_user_data` - 获取用户数据
- `POST /update_user_stats` - 更新用户数值
- `POST /reset_user_data` - 重置用户数据

### 聊天功能
- `POST /chat` - 发送聊天消息
- `POST /get_character_history` - 获取角色聊天历史
- `POST /clear` - 清空聊天历史
- `POST /update_message` - 更新消息内容

### 其他
- `GET /get_characters` - 获取可用角色列表
- `GET /image/<filename>` - 获取角色图片

## 技术栈

- **后端**: Flask, Python
- **前端**: HTML5, CSS3, JavaScript (ES6+)
- **数据存储**: JSON文件
- **AI服务**: OpenAI GPT / Google Gemini

## 开发说明

### 添加新角色

在 `backend/config.py` 的 `game_prompts` 字典中添加新角色的提示词。

### 自定义样式

修改 `frontend/static/css/style.css` 文件来调整界面样式。

### 扩展功能

- 后端API扩展：在 `backend/app.py` 中添加新的路由
- 前端功能扩展：在 `frontend/static/js/app.js` 中添加新的JavaScript函数

## 注意事项

1. 确保两个服务器都正常启动
2. 前端默认连接到 `localhost:5000` 的后端服务
3. 用户数据和聊天历史以JSON格式存储在本地文件中
4. 需要有效的AI API密钥才能正常使用聊天功能

## 版本历史

- v2.0: 前后端分离架构
- v1.0: 单体应用架构
