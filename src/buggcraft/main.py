import os
import sys
from PySide6.QtWidgets import QApplication

from utils.helpers import load_custom_font
from windows.main_window import MinecraftLauncher


def main():
    HOME_PATH = os.path.abspath(os.path.join(os.getcwd(), '../', '../'))

    app = QApplication(sys.argv)
    app.setStyleSheet("QComboBox { qproperty-sizeAdjustPolicy: AdjustToMinimumContentsLengthWithIcon; }")
    load_custom_font(HOME_PATH)  # 加载并设置全局字体
    app.setStyle('Fusion')  # 设置应用程序样式
    
    # 创建并显示启动器
    launcher = MinecraftLauncher(HOME_PATH)
    launcher.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
