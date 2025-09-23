import os

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase

import logging
logger = logging.getLogger(__name__)


def load_custom_font(HOME_PATH: str):
    """加载自定义字体文件并设置为全局字体"""
    # 字体文件路径
    fonts = [
        os.path.abspath(os.path.join(HOME_PATH, 'fonts', 'ChuangKeTieJinGangTi-2.otf')),
        os.path.abspath(os.path.join(HOME_PATH, 'fonts', 'SourceHanSansCN-Heavy.otf')),
        os.path.abspath(os.path.join(HOME_PATH, 'fonts', 'SourceHanSansCN-Medium.ttf')),
    ]
    for font in fonts:
        # 加载字体文件
        font_id = QFontDatabase.addApplicationFont(font)
        if font_id == -1:
            logger.info(f"无法加载字体文件: {font}")
            return
        
        # 获取字体家族名称
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if not font_families:
            logger.info(f"字体文件中未找到有效的字体家族: {font}")
            return
        
        for i in font_families:
            app_font = QFont(i)
            QApplication.setFont(app_font)
            logger.info(f"已设置全局字体: {i}")

