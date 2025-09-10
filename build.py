import os
import subprocess
import sys
import psutil


def build_with_nuitka():
    """使用 Nuitka 进行极致优化打包
    400M优化到13M，后续需要继续优化，可以优化到10M以下"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(current_dir, "src", "buggcraft", "main.py")
    resources_dir = os.path.join(current_dir, "resources")
    icon_path = os.path.join(resources_dir, "icons", "app.ico")
    upx_path = os.path.join('D:\\', 'upx')
    print(upx_path)

    # 确保 UPX 已安装
    try:
        subprocess.run(["upx", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("❌ UPX 未安装，请从 https://upx.github.io/ 下载并添加到 PATH")
        return
    
    import minecraft_launcher_lib

    # 获取库的安装路径
    package_path = os.path.dirname(minecraft_launcher_lib.__file__)
    version_file = os.path.join(package_path, 'version.txt')

    print(f"version.txt 路径: {version_file}")
    command = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        "--standalone",
        f"--jobs={psutil.cpu_count(logical=True)}",
        "--enable-plugin=pyside6",
        "--plugin-enable=upx",
        f"--upx-binary={upx_path}",
        "--disable-ccache",
        f"--windows-icon-from-ico={icon_path}",
        # "--windows-disable-console",
        # "--disable-console",
        "--output-dir=dist",
        "--lto=yes",
        "--python-flag=-O",
        "--python-flag=-S",
        
        # f"--include-data-dir={resources_dir}=resources",
        f"--include-data-files={version_file}=minecraft_launcher_lib/version.txt",
        "--include-package-data=buggcraft=*.py,*.ui,*.qss,*.png,*.jpg,*.svg,*.ico,version.txt",
        "--include-module=psutil",
        "--include-module=notifypy",
        # "--include-module=charset_normalizer",
        "--include-module=PySide6.QtCore",
        "--include-module=PySide6.QtGui",
        "--include-module=PySide6.QtWidgets",
        "--include-module=minecraft_launcher_lib",
        "--include-qt-plugins=platforms,imageformats,styles",

        # 初始运行时强制依赖，不能排除
        # "--nofollow-import-to=shiboken6",
        # "--nofollow-import-to=logging",
        # "--nofollow-import-to=email", #urllib3 http
        # "--nofollow-import-to=xml",  notifypy
        
        # 后期需要移除的，依赖与 minecraft_launcher_lib 模块
        # "--nofollow-import-to=requests",  minecraft_launcher_lib
        # "--nofollow-import-to=certifi",  # requests
        # "--nofollow-import-to=idna",  #requests
        # "--nofollow-import-to=urllib3",  #requests
        # "--nofollow-import-to=urllib3.util", #urllib3
        # "--nofollow-import-to=psutil",  # 待移除，本体10M左右

        # 完全用不到，不需要！
        "--nofollow-import-to=requests.tests",
        "--nofollow-import-to=PIL",
        "--nofollow-import-to=PIL.tests",
        "--nofollow-import-to=unittest",
        "--nofollow-import-to=test",
        "--nofollow-import-to=tkinter",
        "--nofollow-import-to=psutil.tests",  # \        # 新增：排除psutil测试
        "--nofollow-import-to=pip._vendor",  # \         # 新增：排除pip供应商包
        "--nofollow-import-to=setuptools",   #\          # 新增：排除setuptools
        "--nofollow-import-to=zstandard",
        
        "--nofollow-import-to=sqlite3",
        "--nofollow-import-to=unittest.mock",
        "--nofollow-import-to=PySide6.QtNetwork",
        "--nofollow-import-to=PySide6.QtWebEngine",  #  QtWebEngineCore
        "--nofollow-import-to=PySide6.QtWebEngineCore",
        "--nofollow-import-to=PySide6.QtWebEngineWidgets",
        "--nofollow-import-to=PySide6.support",
        "--nofollow-import-to=PySide6.Qt3DRender",
        "--nofollow-import-to=PySide6.QtBluetooth",
        "--nofollow-import-to=selenium.webdriver",
        "--nofollow-import-to=charset_normalizer",
        
        # 初始运行时强制依赖DLL，不能排除
        # "--noinclude-dlls=libssl-3.dll",  # 必须保留
        # "--noinclude-dlls=libffi-8.dll",  # 必须保留
        # "--noinclude-dlls=libcrypto-3.dll",  # 必须保留

        # 移除初始运行时不需要的，后期通过外部资源加载
        "--noinclude-dlls=msvcp140.dll",
        "--noinclude-dlls=msvcp140_1.dll",
        "--noinclude-dlls=msvcp140_2.dll",
        "--noinclude-dlls=msvcp140_codecvt_ids.dll",
        "--noinclude-dlls=shiboken6.abi3.dll",
        "--noinclude-dlls=shiboken6/*.dll",
        "--noinclude-dlls=shiboken6/**/*.dll",

        "--noinclude-dlls=qt6core.dll",
        "--noinclude-dlls=qt6gui.dll",
        "--noinclude-dlls=qt6network.dll",
        "--noinclude-dlls=qt6pdf.dll",
        "--noinclude-dlls=qt6svg.dll",
        "--noinclude-dlls=qt6widgets.dll",
        "--noinclude-dlls=pyside6.abi3.dll",
        "--noinclude-dlls=qsvgicon.dll",
        "--noinclude-dlls=qgif.dll",
        "--noinclude-dlls=qico.dll",
        "--noinclude-dlls=qjpeg.dll",
        "--noinclude-dlls=qpdf.dll",
        "--noinclude-dlls=qsvg.dll",
        "--noinclude-dlls=qtga.dll",
        "--noinclude-dlls=qtiff.dll",
        "--noinclude-dlls=qwbmp.dll",
        "--noinclude-dlls=qwebp.dll",
        "--noinclude-dlls=qdirect2d.dll",
        "--noinclude-dlls=qminimal.dll",
        "--noinclude-dlls=qoffscreen.dll",
        "--noinclude-dlls=qwindows.dll",
        "--noinclude-dlls=qmodernwindowsstyle.dll",
        "--noinclude-dlls=qcertonlybackend.dll",
        "--noinclude-dlls=qopensslbackend.dll",
        "--noinclude-dlls=qschannelbackend.dll",
        "--noinclude-dlls=PySide6/*.dll",
        "--noinclude-dlls=PySide6/**/*.dll",
        "--noinclude-dlls=PySide6/**/**/*.dll",
        "--noinclude-dlls=PySide6/**/**/**/*.dll",

        "--noinclude-qt-plugins=all",
        "--enable-plugin=anti-bloat",  # \               # 新增：启用反臃肿插件（可选）
        # "--follow-imports",
        # "--remove-output",
        "--show-progress",
        main_script
    ]
    
    print("执行命令:")
    print(" ".join(command))
    
    try:
        subprocess.run(command, check=True)
        
        # 获取最终文件大小
        exe_path = os.path.join(current_dir, "dist", "main.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\n✅ 打包完成！最终文件大小: {size_mb:.2f} MB")
            
            # 可选：使用 zstandard 进一步压缩
            try:
                import zstandard as zstd
                compressed_path = exe_path + ".zst"
                cctx = zstd.ZstdCompressor(level=22)
                with open(exe_path, "rb") as f_in:
                    with open(compressed_path, "wb") as f_out:
                        cctx.copy_stream(f_in, f_out)
                compressed_size = os.path.getsize(compressed_path) / (1024 * 1024)
                print(f"✅ Zstandard 压缩后大小: {compressed_size:.2f} MB")
            except ImportError:
                print("⚠️ 未安装 zstandard，跳过额外压缩")
        else:
            print("\n✅ 打包完成！")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败，错误代码: {e.returncode}")

if __name__ == "__main__":
    build_with_nuitka()