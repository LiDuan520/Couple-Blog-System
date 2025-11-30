@echo off
chcp 65001
setlocal enabledelayedexpansion

:: ==============================================
:: 设置项目路径和虚拟环境路径
:: ==============================================
set "PROJECT_PATH=%~dp0"
set "VENV_PATH=%PROJECT_PATH%venv"

:: ==============================================
:: 创建虚拟环境（如果不存在）
:: ==============================================
if not exist "%VENV_PATH%" (
    echo 创建虚拟环境...
    python -m venv "%VENV_PATH%"
) else (
    echo 虚拟环境已存在
)

:: 激活虚拟环境
echo 激活虚拟环境...
call "%VENV_PATH%\Scripts\activate.bat"

:: 升级 pip、setuptools、wheel
echo 升级 pip、setuptools、wheel...
python -m pip install --upgrade pip setuptools wheel >nul

:: ==============================================
:: 依赖列表
:: 格式: 包名==版本
:: ==============================================
set "PACKAGES=fastapi==0.95.2 uvicorn==0.23.2 starlette==0.27.0 typing-extensions==4.6.0 anyio==4.12.0 exceptiongroup==1.3.1 colorama==0.4.6 h11==0.16.0 python-dotenv==1.0.0 pyyaml==6.0.3 pydantic==1.10.12"

echo 安装依赖（只安装缺失或版本不匹配的包）...

for %%P in (%PACKAGES%) do (
    set "NAME=%%~P"
    set "TARGET_VER=%%~P"
    for /f "tokens=1,2 delims==" %%A in ("%%P") do (
        set "PKG=%%A"
        set "VER=%%B"
    )
    
    set "INSTALLED_VER="
    for /f "tokens=2 delims=:" %%V in ('python -m pip show !PKG! 2^>nul ^| findstr Version') do (
        set "INSTALLED_VER=%%V"
    )

    if "!INSTALLED_VER!"=="" (
        echo 安装 !PKG!==!VER! ...
        python -m pip install !PKG!==!VER! >nul
    ) else (
        if "!INSTALLED_VER!"=="!VER!" (
            echo !PKG! 已安装，版本正确: !INSTALLED_VER!
        ) else (
            echo !PKG! 版本不匹配: 已安装 !INSTALLED_VER!, 需要 !VER! -> 更新中...
            python -m pip install !PKG!==!VER! >nul
        )
    )
)

:: ==============================================
:: 显示已安装包版本
:: ==============================================
echo.
echo 安装完成，已安装包版本如下：
for %%P in (%PACKAGES%) do (
    for /f "tokens=2 delims=:" %%V in ('python -m pip show %%~P ^| findstr Version') do (
        echo %%~P: %%V
    )
)

:: ==============================================
:: 启动 Uvicorn
:: ==============================================
echo.
echo 启动 Uvicorn...
echo 访问 http://127.0.0.1:8000
python -m uvicorn app.main:app --reload

endlocal
pause
