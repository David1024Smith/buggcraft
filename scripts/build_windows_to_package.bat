@echo off
setlocal

REM 设置项目根目录
set "PROJECT_ROOT=%~dp0"
@REM cd /d "%PROJECT_ROOT%"

REM 创建虚拟环境（如果不存在）
if not exist "packenv\" (
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
pip install -r requirements.txt
@REM pip install pyinstaller


@REM REM 清理旧构建
@REM if exist "build" rmdir /s /q build
@REM if exist "dist" rmdir /s /q dist

@REM REM 执行打包
@REM pyinstaller FaceCaptureSystem.spec --noconfirm

@REM REM 创建安装程序
@REM if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
@REM     "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup.iss
@REM ) else (
@REM     echo Inno Setup not found, skipping installer creation
@REM )

endlocal