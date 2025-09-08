# 基础页面类
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import Qt
import os

class BasePage(QWidget):
    """页面基类 - 提供通用功能和背景支持"""
    
    def __init__(self, home_path, scale_ratio=1.0, parent=None):
        super().__init__(parent)
        self.home_path = home_path
        self.scale_ratio = scale_ratio
        self.bg_image = None
        
    def set_background(self, image_path):
        """设置页面背景图片"""
        full_path = os.path.abspath(os.path.join(self.home_path, image_path))
        if os.path.exists(full_path):
            self.bg_image = QPixmap(full_path)
        else:
            print(f"背景图片不存在: {full_path}")
            
    def paintEvent(self, event):
        """重绘事件 - 绘制背景"""
        if self.bg_image:
            painter = QPainter(self)
            # 缩放图片以适应窗口
            scaled = self.bg_image.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            # 居中绘制
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        super().paintEvent(event)
