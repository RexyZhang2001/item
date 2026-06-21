@echo off
chcp 65001 >nul
setlocal

rem 打包赤瞳桌面应用为 Windows exe（输出到 chitung-frontend\release\）

set "ROOT=%~dp0.."
set "FRONTEND=%ROOT%\chitung-frontend"
set "TOOLBOX=%ROOT%\agent-toolbox"
set "CENTER=%ROOT%\chitung-center"

echo.
echo ========================================
echo   打包赤瞳安全智能平台 (Windows exe)
echo ========================================
echo.

if not exist "%FRONTEND%\node_modules\" (
  echo 安装前端依赖...
  pushd "%FRONTEND%"
  call npm install
  if errorlevel 1 goto :fail
  popd
)

echo 构建前端并生成 exe（可能需要几分钟）...
pushd "%FRONTEND%"
call npm run desktop:dist
if errorlevel 1 goto :fail
popd

echo.
echo [完成] exe 已生成:
echo   %FRONTEND%\release\win-unpacked\赤瞳安全智能平台.exe
echo.
echo 安装包 (可选):
echo   %FRONTEND%\release\*.exe
echo.
echo 之后可双击 scripts\打开赤瞳平台.exe.bat 启动
echo.
pause
exit /b 0

:fail
echo.
echo [错误] 打包失败
pause
exit /b 1
