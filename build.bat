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
pip install nuitka
pip install --upgrade nuitka

@REM REM 清理旧构建
@REM if exist "build" rmdir /s /q build
@REM if exist "dist" rmdir /s /q dist
@REM python -m nuitka --clean-cache=all

@REM REM 执行打包
python build.py

@REM python -m nuitka --onefile --standalone --enable-plugin=pyside6 --output-dir=distx --lto=yes --include-data-dir=resources=resources --include-package-data=buggcraft=*.py,*.ui,*.qss,*.png,*.jpg,*.svg,*.ico --include-package=PySide6 --include-package=minecraft_launcher_lib --include-package=psutil --include-package=PIL --include-module=PIL._imaging --include-module=PIL._imagingcms --include-module=PIL._imagingft --include-module=PIL._imagingtk --include-qt-plugins=platforms,imageformats,styles --follow-imports --remove-output --show-progres --windows-icon-from-ico=resources/icons/app.ico src/buggcraft/main.py
