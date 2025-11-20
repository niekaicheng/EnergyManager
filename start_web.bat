@echo off
echo ========================================
echo Energy Manager Web Interface 启动器
echo ========================================
echo.

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: Python未安装或未添加到PATH!
    pause
    exit /b 1
)

echo [1/4] 检查Flask是否已安装...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Flask未安装，正在安装...
    python -m pip install flask flask-cors
) else (
    echo Flask已安装
)

echo.
echo [2/4] 检查数据库...
python -c "import database; conn = database.create_connection(); c = conn.cursor(); c.execute('SELECT COUNT(*) FROM goals'); print('  - Goals:', c.fetchone()[0]); c.execute('SELECT COUNT(*) FROM events'); print('  - Events:', c.fetchone()[0]); c.execute('SELECT COUNT(*) FROM health_metrics'); print('  - Health Metrics:', c.fetchone()[0]); conn.close()"

echo.
echo [3/4] 启动Web服务器...
echo 服务器地址: http://localhost:5000
echo.
echo 提示: 
echo   - 在浏览器中打开: http://localhost:5000
echo   - 按 Ctrl+C 停止服务器
echo.
echo ========================================
echo.

REM 启动服务器
python web_server.py
