import os
import sys
# 




def get_resource_path():
    """
    获取资源的绝对路径，适用于开发环境和打包环境
    
    参数:
        relative_path: 资源相对于项目根目录的路径，如 "images/icon.png"
    
    返回:
        资源的绝对路径
    """
    try:
        # 打包后，Nuitka 会设置 sys._MEIPASS 属性
        base_path = os.path.join(sys._MEIPASS, '..')
    except:
        # 开发环境下，使用当前文件的目录作为基础路径
        base_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', '..'
        )
    
    # 构建资源的绝对路径
    return os.path.abspath(os.path.join(base_path))


def main():
    RESOURCE_HOME_PATH = get_resource_path()
    print('RESOURCE_HOME_PATH', RESOURCE_HOME_PATH)

    from PySide6.QtWidgets import QApplication
    from utils.helpers import load_custom_font
    from windows.main_window import MinecraftLauncher
    
    app = QApplication(sys.argv)
    load_custom_font(RESOURCE_HOME_PATH)  # 加载并设置全局字体
    app.setStyle('Fusion')  # 设置应用程序样式
    
    # 创建并显示启动器
    launcher = MinecraftLauncher(RESOURCE_HOME_PATH)
    launcher.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
