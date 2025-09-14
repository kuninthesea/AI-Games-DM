# TRPG跑团游戏助手 - 部署说明

## 本地运行
双击运行 `startup.py` 或在命令行执行：
```bash
python startup.py
```

## 服务器部署

### 1. 环境要求
- Python 3.7+
- 防火墙开放端口3000和5000

### 2. 安装和启动
```bash
# 克隆或上传项目到服务器
cd AIGame

# 启动服务器
python server_start.py
```

### 3. 访问游戏
- 替换 `{服务器IP}` 为实际的服务器IP地址
- 游戏地址：`http://{服务器IP}:3000`
- API地址：`http://{服务器IP}:5000`

### 4. 防火墙设置

#### Windows服务器
```cmd
# 开放端口3000
netsh advfirewall firewall add rule name="TRPG Frontend" dir=in action=allow protocol=TCP localport=3000

# 开放端口5000  
netsh advfirewall firewall add rule name="TRPG Backend" dir=in action=allow protocol=TCP localport=5000
```

#### Linux服务器
```bash
# 使用ufw
sudo ufw allow 3000
sudo ufw allow 5000

# 或使用iptables
sudo iptables -A INPUT -p tcp --dport 3000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

### 5. 云服务器部署

#### 阿里云/腾讯云/AWS等
1. 在安全组中开放端口3000和5000
2. 确保服务器公网IP可访问
3. 运行 `python server_start.py`
4. 访问 `http://公网IP:3000`

### 6. 域名绑定（可选）
如果有域名，可以配置反向代理：

#### Nginx配置示例
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # API
    location /api/ {
        proxy_pass http://localhost:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 7. 数据备份
数据库文件位置：`backend/game_database.db`
定期备份此文件即可保存所有游戏数据。

### 8. 常见问题

**Q: 无法远程访问？**
A: 检查防火墙设置和端口是否正确开放

**Q: 页面加载但API请求失败？**
A: 确保后端服务(端口5000)正常运行且可访问

**Q: 如何停止服务？**
A: 使用Ctrl+C或在任务管理器中结束Python进程

**Q: 如何修改端口？**
A: 修改frontend/app.py和backend/app.py中的端口配置

### 9. 性能优化
- 生产环境建议使用 Gunicorn 或 uWSGI
- 配置Nginx作为反向代理
- 使用更强大的数据库（如PostgreSQL）

## 支持
如有问题，请检查：
1. Python版本是否兼容
2. 依赖包是否正确安装
3. 端口是否被占用
4. 防火墙设置是否正确
