import os
import subprocess
import sys
import psutil


def build_with_nuitka():
    """使用 Nuitka 进行极致优化打包"""
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
    
    command = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        "--standalone",
        f"--jobs={psutil.cpu_count(logical=True)}",
        "--enable-plugin=pyside6",
        "--plugin-enable=upx",
        f"--upx-binary={upx_path}",
        # "--best",  # 最大压缩 --upx-compression-level=9或 --best
        "--disable-ccache",
        # "--upx-compression=best",
        f"--windows-icon-from-ico={icon_path}",
        # "--windows-disable-console",
        # "--disable-console",
        "--output-dir=dist",
        "--lto=yes",
        "--python-flag=-O",
        "--python-flag=-S",
        
        f"--include-data-dir={resources_dir}=resources",
        "--include-package-data=buggcraft=*.py,*.ui,*.qss,*.png,*.jpg,*.svg,*.ico",

        "--include-module=PySide6.QtCore",
        "--include-module=PySide6.QtGui",
        "--include-module=PySide6.QtWidgets",
        # "--include-module=PySide6.QtWebEngineWidgets",
        
        "--include-module=psutil",
        "--include-module=minecraft_launcher_lib",
        "--include-module=PIL.Image",
        "--include-module=PIL._imaging",
        "--include-module=PIL._imagingcms",
        "--include-module=PIL._imagingft",
        "--include-module=PIL._imagingtk",

        "--include-qt-plugins=platforms,imageformats,styles",

        # 需要注释的
        # "--nofollow-import-to=shiboken6",
        # "--nofollow-import-to=logging",
        ###########################################

        "--nofollow-import-to=unittest",
        "--nofollow-import-to=test",
        "--nofollow-import-to=tkinter",
        "--nofollow-import-to=psutil.tests",  # \        # 新增：排除psutil测试
        "--nofollow-import-to=pip._vendor",  # \         # 新增：排除pip供应商包
        "--nofollow-import-to=setuptools",   #\          # 新增：排除setuptools
        "--nofollow-import-to=email",   #\          # 新增：排除setuptools
        "--nofollow-import-to=urllib3.util",   #\          # 新增：排除setuptools

        "--nofollow-import-to=zstandard",
        "--nofollow-import-to=xml",
        
        "--nofollow-import-to=sqlite3",
        "--nofollow-import-to=unittest.mock",
        "--nofollow-import-to=PySide6.QtNetwork",
        "--nofollow-import-to=PySide6.QtWebEngine",  #  QtWebEngineCore
        "--nofollow-import-to=PySide6.QtWebEngineCore",
        "--nofollow-import-to=PySide6.QtWebEngineWidgets",
        # "--nofollow-import-to=PySide6.support",
        "--nofollow-import-to=PySide6.Qt3DRender",
        "--nofollow-import-to=PySide6.QtBluetooth",
        "--nofollow-import-to=psutil.tests",
        "--nofollow-import-to=requests",
        "--nofollow-import-to=PIL.tests",
        "--nofollow-import-to=PIL",
        # "--nofollow-import-to=PIL.BlpImagePlugin",
        # "--nofollow-import-to=PIL.BmpImagePlugin",
        # "--nofollow-import-to=PIL.BufrStubImagePlugin",
        # "--nofollow-import-to=PIL.CurImagePlugin",
        # "--nofollow-import-to=PIL.DcxImagePlugin",
        # "--nofollow-import-to=PIL.DdsImagePlugin",
        # "--nofollow-import-to=PIL.EpsImagePlugin",
        # "--nofollow-import-to=PIL.ExifTags",
        # "--nofollow-import-to=PIL.features",
        # "--nofollow-import-to=PIL.FliImagePlugin",
        # "--nofollow-import-to=PIL.FpxImagePlugin",
        # "--nofollow-import-to=PIL.FtexImagePlugin",
        # "--nofollow-import-to=PIL.GbrImagePlugin",
        # "--nofollow-import-to=PIL.GifImagePlugin",
        # "--nofollow-import-to=PIL.GimpGradientFile",
        # "--nofollow-import-to=PIL.GimpPaletteFile",
        # "--nofollow-import-to=PIL.GribStubImagePlugin",
        # "--nofollow-import-to=PIL.Hdf5StubImagePlugin",
        # "--nofollow-import-to=PIL.IcnsImagePlugin",
        # "--nofollow-import-to=PIL.IcoImagePlugin",
        # "--nofollow-import-to=PIL.ImImagePlugin",
        # "--nofollow-import-to=PIL.ImtImagePlugin",
        # "--nofollow-import-to=PIL.IptcImagePlugin",
        # "--nofollow-import-to=PIL.Jpeg2KImagePlugin",
        
        
        "--nofollow-import-to=PIL.GribStubImagePlugin",
        "--nofollow-import-to=PIL.GribStubImagePlugin",
        "--nofollow-import-to=PIL.GribStubImagePlugin",
        "--nofollow-import-to=PIL.GribStubImagePlugin",
        "--nofollow-import-to=PIL.GribStubImagePlugin",
        "--nofollow-import-to=PIL.GribStubImagePlugin",

        "--nofollow-import-to=requests.tests",

        "--nofollow-import-to=certifi",
        "--nofollow-import-to=idna",
        "--nofollow-import-to=urllib3",
        "--nofollow-import-to=selenium.webdriver",
        
        "--nofollow-import-to=charset_normalizer",
        

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