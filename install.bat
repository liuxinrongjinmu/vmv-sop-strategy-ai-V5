@echo off
echo ========================================
echo VMV-SOP战略咨询系统 - 启动脚本
echo ========================================
echo.

echo [1/4] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

echo [2/4] 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Node.js，请先安装Node.js 18+
    pause
    exit /b 1
)

echo [3/4] 安装后端依赖...
cd backend
if not exist ".env" (
    echo 正在创建.env配置文件...
    copy .env.example .env
    echo.
    echo ========================================
    echo 重要提示: 请编辑 backend\.env 文件，填入您的API密钥！
    echo ========================================
    echo.
)
pip install -r requirements.txt
if errorlevel 1 (
    echo 错误: 后端依赖安装失败
    pause
    exit /b 1
)

echo [4/4] 安装前端依赖...
cd ..\frontend
npm install
if errorlevel 1 (
    echo 错误: 前端依赖安装失败
    pause
    exit /b 1
)

cd ..
echo.
echo ========================================
echo 依赖安装完成！
echo ========================================
echo.
echo 启动方式:
echo   1. 后端: cd backend ^&^& python -m uvicorn app.main:app --reload --port 8000
echo   2. 前端: cd frontend ^&^& npm run dev
echo.
echo 或者运行 start.bat 一键启动
echo.
pause
