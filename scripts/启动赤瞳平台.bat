@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

rem 赤瞳安全智能平台 — Windows 一键启动（开发模式）
rem 双击本脚本：启动后端 + Electron 桌面工作台

set "ROOT=%~dp0.."
set "TOOLBOX=%ROOT%\agent-toolbox"
set "CENTER=%ROOT%\chitung-center"
set "FRONTEND=%ROOT%\chitung-frontend"

echo.
echo ========================================
echo   赤瞳安全智能平台
echo ========================================
echo 项目目录: %ROOT%
echo.

if not exist "%FRONTEND%\node_modules\" (
  echo [1/4] 首次运行，安装前端依赖...
  pushd "%FRONTEND%"
  call npm install
  if errorlevel 1 goto :fail
  popd
) else (
  echo [1/4] 前端依赖已就绪
)

if not exist "%TOOLBOX%\.venv\Scripts\python.exe" (
  echo [安装] 创建 agent-toolbox 虚拟环境...
  pushd "%TOOLBOX%"
  python -m venv .venv
  call .venv\Scripts\pip.exe install fastapi "uvicorn[standard]" pydantic pydantic-settings python-dotenv requests httpx pillow pypdfium2 python-docx pycryptodome eval_type_backport
  if errorlevel 1 goto :fail
  popd
)

if not exist "%CENTER%\.venv\Scripts\python.exe" (
  echo [安装] 创建 chitung-center 虚拟环境...
  pushd "%CENTER%"
  python -m venv .venv
  call .venv\Scripts\pip.exe install -r requirements.txt
  if errorlevel 1 goto :fail
  popd
)

if not exist "%TOOLBOX%\.env" (
  call "%~dp0write_local_env.bat" "%ROOT%"
)
if not exist "%FRONTEND%\.env" copy /Y "%FRONTEND%\.env.example" "%FRONTEND%\.env" >nul

echo [2/4] 启动 agent-toolbox (:8899)...
curl -sf http://127.0.0.1:8899/health >nul 2>&1
if errorlevel 1 (
  start "agent-toolbox" /MIN cmd /c "cd /d \"%TOOLBOX%\" && .venv\Scripts\python.exe run_server.py"
)

echo [3/4] 启动 chitung-center (:8999)...
curl -sf http://127.0.0.1:8999/health >nul 2>&1
if errorlevel 1 (
  start "chitung-center" /MIN cmd /c "cd /d \"%CENTER%\" && .venv\Scripts\python.exe run_server.py"
)

echo 等待后端就绪...
set /a WAIT=0
:wait_center
curl -sf http://127.0.0.1:8999/health >nul 2>&1
if not errorlevel 1 goto :backends_ready
set /a WAIT+=1
if !WAIT! GEQ 45 goto :backends_timeout
timeout /t 1 /nobreak >nul
goto :wait_center

:backends_timeout
echo [警告] 中台启动较慢，桌面应用仍将尝试打开...
goto :launch_desktop

:backends_ready
echo [OK] 后端已就绪
echo   工具箱: http://127.0.0.1:8899
echo   中台:   http://127.0.0.1:8999
echo.

:launch_desktop
echo [4/4] 打开赤瞳工作台...
rem 释放可能被占用的 5173 端口，确保只启动一个前端服务
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do (
  taskkill /F /PID %%P >nul 2>&1
)
pushd "%FRONTEND%"
start "chitung-vite" /MIN cmd /c "npm run dev -- --host 127.0.0.1 --port 5173 --strictPort"
echo 等待前端页面就绪...
set /a FRONTEND_WAIT=0
:wait_frontend
curl -sf http://127.0.0.1:5173 >nul 2>&1
if not errorlevel 1 goto :frontend_ready
set /a FRONTEND_WAIT+=1
if !FRONTEND_WAIT! GEQ 30 goto :frontend_timeout
timeout /t 1 /nobreak >nul
goto :wait_frontend

:frontend_ready
echo 前端已就绪，启动 Electron 桌面应用...
if not exist "%FRONTEND%\node_modules\.bin\electron.cmd" (
  echo [错误] 未找到 Electron 运行文件，请先确认前端依赖安装完成
  goto :fail
)
start "chitung-desktop" cmd /c "set VITE_DEV_SERVER_URL=http://127.0.0.1:5173&& set CHITUNG_AUTOSTART_SERVICES=false&& node_modules\.bin\electron.cmd ."
goto :after_frontend

:frontend_timeout
echo [警告] 前端服务启动较慢，暂不打开浏览器。请重新运行本脚本或检查 Vite 输出。

:after_frontend
popd
goto :end

:fail
echo.
echo [错误] 启动失败，请确认已安装 Python 3.11+ 与 Node.js 18+
pause
exit /b 1

:end
endlocal
