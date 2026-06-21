@echo off
chcp 65001 >nul
setlocal

echo.
echo 正在停止赤瞳安全智能平台相关进程...

for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do (
  taskkill /F /PID %%P >nul 2>&1
)

for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8899" ^| findstr "LISTENING"') do (
  taskkill /F /PID %%P >nul 2>&1
)

for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8999" ^| findstr "LISTENING"') do (
  taskkill /F /PID %%P >nul 2>&1
)

taskkill /F /IM electron.exe >nul 2>&1

echo 已停止。浏览器里已经打开的测试页面可以直接关闭。
pause
endlocal
