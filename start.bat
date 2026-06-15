@echo off
echo ========================================
echo VMV-SOP战略咨询系统 - 一键启动（开发模式）
echo ========================================
echo.

echo [1/2] 启动后端服务（开发模式）...
start "Backend Server" cmd /k "cd backend && copy .env.example .env /Y >nul 2>&1 && python -m uvicorn app.main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo [2/2] 启动前端服务...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo 服务启动完成！
echo ========================================
echo.
echo 后端地址: http://localhost:8000
echo 前端地址: http://localhost:5173
echo API文档:  http://localhost:8000/docs
echo.
echo 按任意键打开浏览器...
pause >nul
start http://localhost:5173
