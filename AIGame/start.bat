@echo off
echo 🎲 TRPG跑团游戏助手 - 启动脚本
echo.

echo 正在启动后端服务器...
cd backend
start "TRPG Backend" cmd /k "python app.py"

timeout /t 3 /nobreak >nul

echo 正在启动前端服务器...
cd ..\frontend
start "TRPG Frontend" cmd /k "python app.py"

echo.
echo ✅ 服务已启动！
echo 后端地址: http://localhost:5000
echo 前端地址: http://localhost:3000
echo.
echo 按任意键退出此窗口...
pause >nul
