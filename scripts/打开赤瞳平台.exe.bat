@echo off
chcp 65001 >nul
setlocal

rem 打开已打包的赤瞳桌面 exe（需先运行 build_chitung_exe.bat）

set "ROOT=%~dp0.."
set "EXE_DIR=%ROOT%\chitung-frontend\release\win-unpacked"
set "EXE=%EXE_DIR%\赤瞳安全智能平台.exe"

echo.
echo 赤瞳安全智能平台 — 打开已打包程序
echo.

if not exist "%EXE%" (
  echo 未找到 exe 文件:
  echo   %EXE%
  echo.
  echo 请先双击运行: scripts\build_chitung_exe.bat
  echo.
  pause
  exit /b 1
)

rem 若后端未运行，Electron 主进程会自动拉起（CHITUNG_AUTOSTART_SERVICES 默认开启）
start "" "%EXE%"
echo 已启动: %EXE%
timeout /t 2 /nobreak >nul
exit /b 0
