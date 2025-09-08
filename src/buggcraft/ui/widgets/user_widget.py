# UserWidget 类

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtWidgets import (QWidget, QSizePolicy)


class QMWidget(QWidget):
    """支持背景图片"""
    def __init__(self, background_path, parent=None):
        super().__init__(parent)
        self.background_path = background_path
        self.background_pixmap = QPixmap(background_path)
        
        # 设置尺寸策略：水平方向尽可能扩展，垂直方向固定（由sizeHint决定）
        # 关键：水平 Policy 为 Expanding，垂直 Policy 为 Fixed
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def sizeHint(self):
        """
        重写sizeHint，返回一个建议尺寸。
        布局管理器会参考这个值，特别是当垂直策略为Fixed时。
        这里根据当前控件的宽度和图片的宽高比，动态计算并返回一个建议高度。
        """
        if not self.background_pixmap.isNull():
            # 1. 获取图片原始宽高
            original_size = self.background_pixmap.size()
            pixmap_width = original_size.width()
            pixmap_height = original_size.height()
            pixmap_ratio = pixmap_height / pixmap_width # 计算高宽比

            # 2. 获取控件当前的（或即将的）实际宽度
            current_width = self.width()

            # 3. 根据当前宽度和图片的高宽比，计算期望的高度
            desired_height = int(current_width * pixmap_ratio)

            # 4. 返回计算出的尺寸：宽度为当前宽度，高度为按比例计算出的高度
            return QSize(current_width, desired_height)
        # 如果图片无效，返回一个默认值或父类的实现
        return super().sizeHint()

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.background_pixmap.isNull():
            # 获取控件当前的实际大小
            widget_size = self.size()
            # 使用 KeepAspectRatio 模式进行缩放，确保图片不变形
            scaled_pixmap = self.background_pixmap.scaled(
                widget_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            # 计算图片在控件中居中显示的位置
            x = (widget_size.width() - scaled_pixmap.width()) // 2
            y = (widget_size.height() - scaled_pixmap.height()) // 2
            # 绘制图片
            painter.drawPixmap(x, y, scaled_pixmap)
        super().paintEvent(event)
